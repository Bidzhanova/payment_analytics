import os
import logging
import argparse
import sys
from typing import Tuple, Optional, Set
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from config.settings import INPUT_FILE, OUTPUT_EXCEL, OUTPUT_PLOT, PLOT_SETTINGS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('payment_analytics.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def validate_data(df: pd.DataFrame, sheet_name: str, required_columns: Optional[Set[str]] = None) -> None:
    """Проверяет данные на валидность.

    Args:
        df: DataFrame для проверки
        sheet_name: Имя листа для логов
        required_columns: Множество обязательных колонок
    Raises:
        ValueError: Если данные не прошли валидацию
    """
    if df.empty:
        raise ValueError(f"Лист '{sheet_name}' пуст!")

    if df.isnull().values.any():
        logger.warning(f"Обнаружены пропущенные значения в листе '{sheet_name}'")

    if required_columns:
        missing_cols = required_columns - set(df.columns)
        if missing_cols:
            raise ValueError(
                f"В листе '{sheet_name}' отсутствуют колонки: {missing_cols}"
            )


def clean_data(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    """Обрабатывает пропущенные значения.

    Args:
        df: DataFrame для очистки
        sheet_name: Имя листа для логов
    Returns:
        Очищенный DataFrame
    """
    if df.isnull().values.any():
        logger.info(f"Очистка данных в листе '{sheet_name}'")

        # Заполняет числовые колонки
        num_cols = df.select_dtypes(include='number').columns
        df[num_cols] = df[num_cols].fillna(0)

        # Заполняет категориальные колонки
        cat_cols = df.select_dtypes(exclude='number').columns
        df[cat_cols] = df[cat_cols].fillna('Unknown')

        # Специфичная очистка для method_group
        if 'method_in_dwh' in df.columns:
            df['method_in_dwh'] = df['method_in_dwh'].fillna('unknown_method')

    return df


def load_data(filepath: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Загружает, проверяет и очищает данные."""
    try:
        # Проверка файла
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Файл {filepath} не найден!")

        # Проверка листов
        required_sheets = {'data', 'country', 'method_group'}
        with pd.ExcelFile(filepath) as excel:
            missing_sheets = required_sheets - set(excel.sheet_names)
            if missing_sheets:
                raise ValueError(f"Отсутствуют листы: {missing_sheets}")

            # Загрузка
            df = pd.read_excel(filepath, sheet_name='data')
            countries = pd.read_excel(filepath, sheet_name='country')
            methods = pd.read_excel(filepath, sheet_name='method_group')

        # Валидация
        validate_data(df, 'data', {'month', 'currency', 'method', 'total transactions'})
        validate_data(countries, 'country', {'currency', 'country'})
        validate_data(methods, 'method_group', {'method_in_dwh', 'method_group'})

        # Очистка
        df = clean_data(df, 'data')
        countries = clean_data(countries, 'country')
        methods = clean_data(methods, 'method_group')

        logger.info("Данные успешно загружены и обработаны")
        return df, countries, methods

    except Exception as e:
        logger.error(f"Ошибка загрузки: {str(e)}")
        raise


def merge_and_calculate(
        df: pd.DataFrame,
        countries: pd.DataFrame,
        methods: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Объединяет данные и вычисляет статистику."""
    try:
        # Слияние данных
        df_with_countries = pd.merge(df, countries, on='currency', how='left')
        df_with_methods = pd.merge(df, methods, left_on='method', right_on='method_in_dwh', how='left')

        # Расчет статистики
        monthly_stats = df.groupby('month').agg({
            'total transactions': 'sum',
            'approved_ transactions': 'sum',
            'volume_usd': 'sum'
        }).reset_index()
        monthly_stats['approval_rate'] = (
                monthly_stats['approved_ transactions'] /
                monthly_stats['total transactions'].replace(0, 1)  # Защита от деления на 0
        )

        country_stats = df_with_countries.groupby('country').agg({
            'total transactions': 'sum',
            'approved_ transactions': 'sum',
            'volume_usd': 'sum'
        }).reset_index()
        country_stats['approval_rate'] = (
                country_stats['approved_ transactions'] /
                country_stats['total transactions'].replace(0, 1)
        )

        method_stats = df_with_methods.groupby('method_group').agg({
            'total transactions': 'sum',
            'approved_ transactions': 'sum',
            'volume_usd': 'sum'
        }).reset_index()
        method_stats['approval_rate'] = (
                method_stats['approved_ transactions'] /
                method_stats['total transactions'].replace(0, 1))

        logger.info("Статистика успешно рассчитана")
        return monthly_stats, country_stats, method_stats

    except Exception as e:
        logger.error(f"Ошибка расчета статистики: {str(e)}")
        raise


def create_combined_plot(
        monthly_stats: pd.DataFrame,
        country_stats: pd.DataFrame,
        method_stats: pd.DataFrame,
        plot_path: str
) -> None:
    """Создает комбинированный график."""
    try:
        # Установка стиля
        plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'seaborn')

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        palette = 'viridis'

        # 1. Топ-10 стран по объему (USD)
        if not country_stats.empty:
            top_countries = country_stats.nlargest(10, 'volume_usd')
            ax = sns.barplot(
                ax=axes[0, 0],
                x='volume_usd',
                y='country',
                hue='country',
                data=top_countries,
                palette=palette,
                dodge=False,
                legend=False
            )

            # Подписи значений внутри столбцов
            for p in ax.patches:
                width = p.get_width()
                label = f'{width:,.0f}'.replace(",", " ")

                # Позиционирование по центру столбца
                x_pos = width / 2
                y_pos = p.get_y() + p.get_height() / 2.

                text_color = 'white'

                ax.text(x_pos, y_pos, label,
                        va='center', ha='center',
                        fontsize=10, color=text_color,
                        fontweight='bold')  # Полужирный для лучшей читаемости

            axes[0, 0].set_title('Топ-10 стран по объему транзакций (USD)', pad=20, fontsize=18, fontweight='bold')
            axes[0, 0].set_xlabel('')  # Убирает подпись оси X
            axes[0, 0].set_ylabel('')
            axes[0, 0].set_xlim(0, top_countries['volume_usd'].max() * 1.15)  # Расширение для подписей
            axes[0, 0].set_xticklabels([])  # Убирает цифры на оси X
            axes[0, 0].tick_params(axis='x', which='both', length=0)  # Убирает деления

            # 2. Процент одобрения по странам
            if not country_stats.empty:
                top_approval = country_stats.nlargest(10, 'approval_rate')
                ax = sns.barplot(
                    ax=axes[0, 1],
                    x='approval_rate',
                    y='country',
                    hue='country',
                    data=top_approval,
                    palette=palette,
                    dodge=False,
                    legend=False
                )

                # Подписи значений внутри столбцов
                for p in ax.patches:
                    width = p.get_width()
                    label = f'{width * 100:.2f}%' # Формат 00.00%

                    # Позиционирование по центру столбца
                    x_pos = width / 2
                    y_pos = p.get_y() + p.get_height() / 2.

                    text_color = 'white'

                    ax.text(x_pos, y_pos, label,
                            va='center', ha='center',
                            fontsize=10, color=text_color,
                            fontweight='bold')  # Полужирный для лучшей читаемости

                axes[0, 1].set_title('Топ-10 стран по проценту одобрения', pad=20, fontsize=18, fontweight='bold')
                axes[0, 1].set_xlabel('')  # Убирает подпись оси X
                axes[0, 1].set_ylabel('')
                axes[0, 1].set_xlim(0, 1.15)
                axes[0, 1].set_xticklabels([])  # Убирает цифры на оси X
                axes[0, 1].tick_params(axis='x', which='both', length=0)  # Убирает деления

            # 3. Методы платежей
            if not method_stats.empty:
                method_stats_sorted = method_stats.sort_values('volume_usd', ascending=False)
                ax = sns.barplot(
                    ax=axes[1, 0],
                    x='method_group',
                    y='volume_usd',
                    hue='method_group',
                    data=method_stats_sorted,
                    palette=palette,
                    dodge=False,
                    legend=False
                )

                # Добавление подписи значений над столбцами
                for p in ax.patches:
                    height = p.get_height()
                    ax.text(p.get_x() + p.get_width() / 2., height + height * 0.05,
                            f'{height:,.0f}'.replace(",", " "),  # Формат 1 000 000
                            ha='center', va='bottom', fontsize=10, fontweight='bold')

                axes[1, 0].set_title('Объем транзакций по методам платежа (USD)', pad=20, fontsize=18, fontweight='bold')
                axes[1, 0].set_xlabel('')
                axes[1, 0].set_ylabel('')
                axes[1, 0].set_yticklabels([])  # Убирает подписи на оси Y
                axes[1, 0].tick_params(axis='y', which='both', length=0)  # Убирает деления

        # 4. Одобрение по месяцам (USD)
        if not monthly_stats.empty:
            monthly_stats = monthly_stats.copy()
            monthly_stats['month'] = pd.to_datetime(monthly_stats['month'])
            monthly_stats = monthly_stats.sort_values('month')
            monthly_stats['month_str'] = monthly_stats['month'].dt.strftime('%Y-%m')

            # Создание графика
            ax = sns.barplot(
                ax=axes[1, 1],
                x='month_str',
                y='approval_rate',
                hue='month_str',
                data=monthly_stats,
                palette=palette,
                dodge=False,
                legend=False
            )

            # Подписи процентов внутри столбцов
            for p in ax.patches:
                height = p.get_height()
                if height > 0:  # Не отображаем подписи для нулевых значений
                    # Позиция по вертикали - 50% высоты столбца
                    y_pos = height * 0.5
                    label = f'{height * 100:.2f}%'

                    text_color = 'white'

                    ax.text(p.get_x() + p.get_width() / 2., y_pos, label,
                            ha='center', va='center', fontsize=12,
                            color=text_color, fontweight='bold')

        axes[1, 1].set_title('Процент одобрения по месяцам', pad=20, fontsize=18, fontweight='bold')
        axes[1, 1].set_xlabel('')
        axes[1, 1].set_ylabel('')
        axes[1, 1].set_ylim(0, 1.1)

        # Убирает все отметки и подписи на оси Y
        axes[1, 1].set_yticklabels([])
        axes[1, 1].tick_params(axis='y', which='both', length=0)  # Убирает деления


        # Общие улучшения для всех графиков
        for ax in axes.flat:
            ax.grid(True, linestyle='--', alpha=0.6)
            for spine in ['top', 'right']:
                ax.spines[spine].set_visible(False)

        # Сохранение
        ensure_directory_exists(plot_path)
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"График сохранен в {plot_path}")

    except Exception as e:
        logger.error(f"Ошибка построения графика: {str(e)}")
        raise


def ensure_directory_exists(path: str) -> None:
    """Создает директорию при необходимости."""
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
        logger.info(f"Создана директория: {dir_path}")


def save_to_excel(
        monthly_stats: pd.DataFrame,
        country_stats: pd.DataFrame,
        method_stats: pd.DataFrame,
        output_file: str
) -> None:
    """Сохраняет данные в Excel."""
    try:
        ensure_directory_exists(output_file)
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            monthly_stats.to_excel(writer, sheet_name='Monthly', index=False)
            country_stats.to_excel(writer, sheet_name='Countries', index=False)
            method_stats.to_excel(writer, sheet_name='Methods', index=False)
        logger.info(f"Данные сохранены в {output_file}")
    except Exception as e:
        logger.error(f"Ошибка сохранения Excel: {str(e)}")
        raise


def main():
    try:
        parser = argparse.ArgumentParser(description='Анализ платежных транзакций')
        parser.add_argument('--input', default=INPUT_FILE, help='Путь к входному файлу')
        parser.add_argument('--output-excel', default=OUTPUT_EXCEL, help='Путь для Excel')
        parser.add_argument('--output-plot', default=OUTPUT_PLOT, help='Путь для графика')
        args = parser.parse_args()

        logger.info("=" * 50)
        logger.info("Запуск анализа платежных данных")
        logger.info(f"Входной файл: {args.input}")

        # Загрузка и обработка данных
        df, countries, methods = load_data(args.input)
        monthly_stats, country_stats, method_stats = merge_and_calculate(df, countries, methods)

        # Визуализация и сохранение
        create_combined_plot(monthly_stats, country_stats, method_stats, args.output_plot)
        save_to_excel(monthly_stats, country_stats, method_stats, args.output_excel)

        logger.info("Анализ успешно завершен!")
        logger.info(f"Результаты сохранены в:\n- {args.output_excel}\n- {args.output_plot}")
        logger.info("=" * 50)

    except Exception as e:
        logger.critical(f"Фатальная ошибка: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
