import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


def create_combined_plot(
        monthly_stats: pd.DataFrame,
        country_stats: pd.DataFrame,
        method_stats: pd.DataFrame,
        output_path: Optional[str] = None
) -> None:
    """
    Создает и сохраняет комбинированный график с 4 диаграммами:
    1. Топ-10 стран по объему транзакций
    2. Топ-10 стран по проценту одобрения
    3. Объем транзакций по методам платежа
    4. Процент одобрения по месяцам

    Args:
        monthly_stats: DataFrame с месячной статистикой
        country_stats: DataFrame со статистикой по странам
        method_stats: DataFrame со статистикой по методам платежа
        output_path: Путь для сохранения графика (если None - берется из настроек)
    """
    try:
        output_path = output_path or settings.OUTPUT_PLOT
        _ensure_directory_exists(output_path)

        # Настройка стиля
        _setup_plot_style()

        # Создание фигуры
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle("Анализ платежных транзакций", fontsize=28, fontweight='bold', y=1.02)

        # Построение графиков
        _plot_top_countries_volume(country_stats, axes[0, 0])
        _plot_top_countries_approval(country_stats, axes[0, 1])
        _plot_payment_methods(method_stats, axes[1, 0])
        _plot_monthly_approval(monthly_stats, axes[1, 1])

        # Оптимизация расположения и сохранение
        plt.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        logger.info(f"График успешно сохранен: {output_path}")

    except Exception as e:
        logger.error(f"Ошибка при построении графика: {str(e)}")
        raise


def _setup_plot_style() -> None:
    """Настраивает единый стиль для всех графиков"""
    plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'seaborn')
    sns.set_palette("viridis")
    plt.rcParams.update({
        'font.size': 12,
        'axes.titlesize': 16,
        'axes.labelweight': 'bold',
        'figure.autolayout': True
    })


def _ensure_directory_exists(path: str) -> None:
    """Создает директорию для сохранения графика при необходимости"""
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
        logger.debug(f"Создана директория: {dir_path}")


def _plot_top_countries_volume(
        country_stats: pd.DataFrame,
        ax: plt.Axes
) -> None:
    """Строит график топ-10 стран по объему транзакций"""
    if country_stats.empty:
        return

    top_countries = country_stats.nlargest(10, 'volume_usd')
    plot = sns.barplot(
        ax=ax,
        x='volume_usd',
        y='country',
        data=top_countries,
        hue='country',
        palette='viridis',
        dodge=False,
        legend=False
    )

    # Подписи значений
    for p in plot.patches:
        width = p.get_width()
        ax.text(
            width / 2,
            p.get_y() + p.get_height() / 2,
            f'{width:,.0f}'.replace(",", " "),
            va='center',
            ha='center',
            fontsize=12,
            color='white',
            fontweight='bold'
        )

    # Настройка внешнего вида
    ax.set_title('Топ-10 стран по объему транзакций (USD)', pad=20, fontsize=18, fontweight='bold')
    ax.set_xlabel('')
    ax.set_ylabel('')

    # Увеличение размера подписей стран на оси Y
    ax.tick_params(axis='y', which='major', labelsize=12)  # Размер шрифта

    ax.set_xlim(0, top_countries['volume_usd'].max() * 1.15)
    ax.set_xticklabels([])
    ax.tick_params(axis='x', which='both', length=0)
    ax.grid(True, linestyle='--', alpha=0.6)


def _plot_top_countries_approval(
        country_stats: pd.DataFrame,
        ax: plt.Axes
) -> None:
    """Строит график топ-10 стран по проценту одобрения"""
    if country_stats.empty:
        return

    top_approval = country_stats.nlargest(10, 'approval_rate')
    plot = sns.barplot(
        ax=ax,
        x='approval_rate',
        y='country',
        data=top_approval,
        hue='country',
        palette='viridis',
        dodge=False,
        legend=False
    )

    # Подписи значений
    for p in plot.patches:
        width = p.get_width()
        ax.text(
            width / 2,
            p.get_y() + p.get_height() / 2,
            f'{width * 100:.2f}%',
            va='center',
            ha='center',
            fontsize=12,
            color='white',
            fontweight='bold'
        )

    # Настройка внешнего вида
    ax.set_title('Топ-10 стран по проценту одобрения', pad=20, fontsize=18, fontweight='bold')
    ax.set_xlabel('')
    ax.set_ylabel('')

    # Увеличение размера подписей стран на оси Y
    ax.tick_params(axis='y', which='major', labelsize=12)  # Размер шрифта

    ax.set_xlim(0, 1.15)
    ax.set_xticklabels([])
    ax.tick_params(axis='x', which='both', length=0)
    ax.grid(True, linestyle='--', alpha=0.6)


def _plot_payment_methods(
        method_stats: pd.DataFrame,
        ax: plt.Axes
) -> None:
    """Строит график объема транзакций по методам платежа"""
    if method_stats.empty:
        return

    method_stats_sorted = method_stats.sort_values('volume_usd', ascending=False)
    plot = sns.barplot(
        ax=ax,
        x='method_group',
        y='volume_usd',
        data=method_stats_sorted,
        hue='method_group',
        palette='viridis',
        dodge=False,
        legend=False
    )

    # Подписи значений
    for p in plot.patches:
        height = p.get_height()
        ax.text(
            p.get_x() + p.get_width() / 2.,
            height + height * 0.05,
            f'{height:,.0f}'.replace(",", " "),
            ha='center',
            va='bottom',
            fontsize=12,
            fontweight='bold'
        )

    # Настройка внешнего вида
    ax.set_title('Объем транзакций по методам платежа (USD)', pad=20, fontsize=18, fontweight='bold')
    ax.set_xlabel('')
    ax.set_ylabel('')

    # Увеличение размера подписей на оси X
    ax.tick_params(axis='x', which='major', labelsize=13)

    ax.set_yticklabels([])
    ax.tick_params(axis='y', which='both', length=0)
    ax.grid(True, linestyle='--', alpha=0.6)


def _plot_monthly_approval(
        monthly_stats: pd.DataFrame,
        ax: plt.Axes
) -> None:
    """Строит график процента одобрения по месяцам"""
    if monthly_stats.empty:
        return

    monthly_stats = monthly_stats.copy()
    monthly_stats['month'] = pd.to_datetime(monthly_stats['month'])
    monthly_stats = monthly_stats.sort_values('month')
    monthly_stats['month_str'] = monthly_stats['month'].dt.strftime('%Y-%m')

    plot = sns.barplot(
        ax=ax,
        x='month_str',
        y='approval_rate',
        data=monthly_stats,
        hue='month_str',
        palette='viridis',
        dodge=False,
        legend=False
    )

    # Подписи значений
    for p in plot.patches:
        height = p.get_height()
        if height > 0:
            ax.text(
                p.get_x() + p.get_width() / 2.,
                height * 0.5,
                f'{height * 100:.2f}%',
                ha='center',
                va='center',
                fontsize=16,
                color='white',
                fontweight='bold'
            )

    # Настройка внешнего вида
    ax.set_title('Процент одобрения по месяцам', pad=20, fontsize=18, fontweight='bold')
    ax.set_xlabel('')
    ax.set_ylabel('')

    # Увеличение размера подписей на оси X
    ax.tick_params(axis='x', which='major', labelsize=13)

    ax.set_ylim(0, 1.1)
    ax.set_yticklabels([])
    ax.tick_params(axis='y', which='both', length=0)
    ax.grid(True, linestyle='--', alpha=0.6)
