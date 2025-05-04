import os
import pandas as pd
from typing import Tuple
from config.settings import settings
from srs.validation import validate_data, clean_data


def load_and_prepare_data(filepath: str = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Основная функция загрузки и подготовки данных"""
    filepath = filepath or settings.INPUT_FILE

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Файл {filepath} не найден")

    df, countries, methods = _load_excel_sheets(filepath)

    # Валидация
    validate_data(df, 'data', {'month', 'currency', 'method', 'total transactions'})
    validate_data(countries, 'country', {'currency', 'country'})
    validate_data(methods, 'method_group', {'method_in_dwh', 'method_group'})

    # Очистка
    df = clean_data(df, 'data')
    countries = clean_data(countries, 'country')
    methods = clean_data(methods, 'method_group')

    return df, countries, methods


def _load_excel_sheets(filepath: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Загружает листы из Excel файла"""
    required_sheets = {'data', 'country', 'method_group'}

    with pd.ExcelFile(filepath) as excel:
        missing_sheets = required_sheets - set(excel.sheet_names)
        if missing_sheets:
            raise ValueError(f"Отсутствуют листы: {missing_sheets}")

        return (
            pd.read_excel(excel, sheet_name='data'),
            pd.read_excel(excel, sheet_name='country'),
            pd.read_excel(excel, sheet_name='method_group')
        )
