import argparse
import logging
import sys
from typing import Tuple

import pandas as pd

from srs.data_loading import load_and_prepare_data
from srs.vizualization import create_combined_plot
from config.settings import settings

# Настройка логирования
def setup_logging() -> logging.Logger:
    """Конфигурирует систему логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('payment_analytics.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """Парсит аргументы командной строки"""
    parser = argparse.ArgumentParser(description='Анализ платежных транзакций')
    parser.add_argument(
        '--input',
        default=settings.INPUT_FILE,
        help='Путь к входному файлу (по умолчанию: %(default)s)'
    )
    parser.add_argument(
        '--output-excel',
        default=settings.OUTPUT_EXCEL,
        help='Путь для сохранения Excel (по умолчанию: %(default)s)'
    )
    parser.add_argument(
        '--output-plot',
        default=settings.OUTPUT_PLOT,
        help='Путь для сохранения графика (по умолчанию: %(default)s)'
    )
    return parser.parse_args()

def calculate_stats(
    df: pd.DataFrame,
    countries: pd.DataFrame,
    methods: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Вычисляет ключевую статистику:
    - По месяцам
    - По странам
    - По методам платежа
    """
    try:
        # Статистика по месяцам
        monthly_stats = df.groupby('month').agg({
            'total transactions': 'sum',
            'approved_ transactions': 'sum',
            'volume_usd': 'sum'
        }).reset_index()
        monthly_stats['approval_rate'] = (
            monthly_stats['approved_ transactions'] /
            monthly_stats['total transactions'].replace(0, 1)
        )

        # Статистика по странам
        df_with_countries = pd.merge(df, countries, on='currency', how='left')
        country_stats = df_with_countries.groupby('country').agg({
            'total transactions': 'sum',
            'approved_ transactions': 'sum',
            'volume_usd': 'sum'
        }).reset_index()
        country_stats['approval_rate'] = (
            country_stats['approved_ transactions'] /
            country_stats['total transactions'].replace(0, 1)
        )

        # Статистика по методам платежа
        df_with_methods = pd.merge(df, methods, left_on='method', right_on='method_in_dwh', how='left')
        method_stats = df_with_methods.groupby('method_group').agg({
            'total transactions': 'sum',
            'approved_ transactions': 'sum',
            'volume_usd': 'sum'
        }).reset_index()
        method_stats['approval_rate'] = (
            method_stats['approved_ transactions'] /
            method_stats['total transactions'].replace(0, 1)
        )

        return monthly_stats, country_stats, method_stats

    except Exception as e:
        raise RuntimeError(f"Ошибка расчета статистики: {str(e)}")

def save_to_excel(
    monthly_stats: pd.DataFrame,
    country_stats: pd.DataFrame,
    method_stats: pd.DataFrame,
    output_file: str
) -> None:
    """Сохраняет результаты анализа в Excel файл"""
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            monthly_stats.to_excel(writer, sheet_name='Monthly', index=False)
            country_stats.to_excel(writer, sheet_name='Countries', index=False)
            method_stats.to_excel(writer, sheet_name='Methods', index=False)
    except Exception as e:
        raise RuntimeError(f"Ошибка сохранения Excel: {str(e)}")

def main() -> None:
    """Основная функция выполнения анализа"""
    logger = setup_logging()
    args = parse_args()

    try:
        logger.info("=" * 50)
        logger.info("Запуск анализа платежных данных")
        logger.info(f"Входной файл: {args.input}")
        logger.info(f"Выходной Excel: {args.output_excel}")
        logger.info(f"Выходной график: {args.output_plot}")

        # 1. Загрузка и подготовка данных
        df, countries, methods = load_and_prepare_data(args.input)
        logger.info("Данные успешно загружены и проверены")

        # 2. Расчет статистики
        monthly_stats, country_stats, method_stats = calculate_stats(df, countries, methods)
        logger.info("Статистика успешно рассчитана")

        # 3. Визуализация
        create_combined_plot(monthly_stats, country_stats, method_stats, args.output_plot)
        logger.info(f"График сохранен: {args.output_plot}")

        # 4. Сохранение в Excel
        save_to_excel(monthly_stats, country_stats, method_stats, args.output_excel)
        logger.info(f"Результаты сохранены в Excel: {args.output_excel}")

        logger.info("Анализ успешно завершен!")
        logger.info("=" * 50)

    except FileNotFoundError as e:
        logger.critical(f"Файл не найден: {str(e)}")
        sys.exit(1)
    except pd.errors.EmptyDataError:
        logger.critical("Ошибка: входной файл не содержит данных")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
