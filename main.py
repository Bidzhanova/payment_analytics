import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt


def load_data(filepath):
    """Загружает данные из листов data, country, method_group."""
    df = pd.read_excel(filepath, sheet_name='data')
    countries = pd.read_excel(filepath, sheet_name='country')
    methods = pd.read_excel(filepath, sheet_name='method_group')
    return df, countries, methods


def merge_and_calculate(df, countries, methods):
    """Объединяет данные и вычисляет необходимую статистику."""
    df_with_countries = pd.merge(df, countries, on='currency', how='left')
    df_with_methods = pd.merge(df, methods, left_on='method', right_on='method_in_dwh', how='left')

    monthly_stats = df.groupby('month').agg({
        'total transactions': 'sum',
        'approved_ transactions': 'sum',
        'volume_usd': 'sum'
    }).reset_index()
    monthly_stats['approval_rate'] = monthly_stats['approved_ transactions'] / monthly_stats['total transactions']

    country_stats = df_with_countries.groupby('country').agg({
        'total transactions': 'sum',
        'approved_ transactions': 'sum',
        'volume_usd': 'sum'
    }).reset_index()
    country_stats['approval_rate'] = country_stats['approved_ transactions'] / country_stats['total transactions']

    method_stats = df_with_methods.groupby('method_group').agg({
        'total transactions': 'sum',
        'approved_ transactions': 'sum',
        'volume_usd': 'sum'
    }).reset_index()
    method_stats['approval_rate'] = method_stats['approved_ transactions'] / method_stats['total transactions']

    return monthly_stats, country_stats, method_stats


def create_combined_plot(monthly_stats, country_stats, method_stats, plt_path):
    """Создает комбинированный график и возвращает его как изображение."""
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    plt.subplots_adjust(hspace=0.45, wspace=0.2)

    # 1. Топ-10 стран по объему транзакций
    top_countries = country_stats.sort_values('volume_usd', ascending=False).head(10)
    ax1 = sns.barplot(
        ax=axes[0, 0],
        x='volume_usd',
        y='country',
        hue='country',
        data=top_countries,
        palette='viridis',
        legend=False
    )

    # Форматирование оси X
    ax1.set_xticks(ax1.get_xticks())  # Устанавливаем явно позиции тиков
    ax1.set_xticklabels([f'{int(x / 1_000_000)} млн' for x in ax1.get_xticks()])  # Формат в миллионах
    ax1.tick_params(axis='x', rotation=45, labelsize=10)  # Добавляем поворот подписей на 45 градусов и выравнивание

    # Настройки заголовков и подписей
    axes[0, 0].set_title('Топ-10 стран по объему транзакций (USD)', fontsize=12)
    axes[0, 0].set_xlabel('Объем (USD)', fontsize=10)
    axes[0, 0].set_ylabel('Страна', fontsize=10)

    # 2. Процент одобрения по странам (топ-10)
    top_approval = country_stats.sort_values('approval_rate', ascending=False).head(10)
    sns.barplot(
        ax=axes[0, 1],
        x='approval_rate',
        y='country',
        hue='country',
        data=top_approval,
        palette='viridis',
        legend=False
    )
    axes[0, 1].set_title('Процент одобрения по странам (топ-10)', fontsize=12)
    axes[0, 1].set_xlabel('Процент одобрения', fontsize=10)
    axes[0, 1].set_ylabel('Страна', fontsize=10)

    # 3. Распределение методов платежа
    method_stats_sorted = method_stats.sort_values('volume_usd', ascending=False)
    ax3 = sns.barplot(
        ax=axes[1, 0],
        x='volume_usd',
        y='method_group',
        hue='method_group',
        data=method_stats_sorted,
        palette='viridis',
        order=method_stats_sorted['method_group'],
        legend=False
    )

    # Форматирование оси X
    ax3.set_xticks(ax3.get_xticks())
    ax3.set_xticklabels([f'{int(x / 1_000_000)} млн' for x in ax3.get_xticks()])
    ax3.tick_params(axis='x', rotation=45, labelsize=10)

    # Настройки заголовков и подписей
    axes[1, 0].set_title('Объем транзакций по методам платежа', fontsize=12)
    axes[1, 0].set_xlabel('Объем (USD)', fontsize=10)
    axes[1, 0].set_ylabel('Метод платежа', fontsize=10)

    # 4. Сравнение месяцев
    sns.barplot(ax=axes[1, 1], x='month', y='approval_rate', hue='approval_rate', data=monthly_stats, palette='viridis', legend=False)
    axes[1, 1].set_title('Процент одобрения по месяцам', fontsize=12)
    axes[1, 1].set_xlabel('Месяц', fontsize=10)
    axes[1, 1].set_ylabel('Процент одобрения', fontsize=10)

    plt.savefig(plt_path, format='png', bbox_inches='tight', dpi=150)
    print(f"График сохранен.")


def save_to_excel(monthly_stats, country_stats, method_stats, output_file):
    """Сохраняет данные в Excel файл."""
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        monthly_stats.to_excel(writer, sheet_name='Monthly statistics', index=False)
        country_stats.to_excel(writer, sheet_name='Country statistics', index=False)
        method_stats.to_excel(writer, sheet_name='Method statistics', index=False)


def main():
    # Извлечение данных из файла
    filepath = 'srs/тестовое 2.xlsx'
    df, countries, methods = load_data(filepath)

    plot_path = 'dst/combined_plot.png'

    # Анализ
    monthly_stats, country_stats, method_stats = merge_and_calculate(df, countries, methods)

    # Создание комбинированного графика
    create_combined_plot(monthly_stats, country_stats, method_stats, plot_path)

    # Сохранение в один файл
    save_to_excel(monthly_stats, country_stats, method_stats, 'dst/data analysis.xlsx')


if __name__ == "__main__":
    main()
