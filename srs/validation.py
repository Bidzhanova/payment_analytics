import pandas as pd
from typing import Set, Optional
import logging

logger = logging.getLogger(__name__)


def validate_data(df: pd.DataFrame, sheet_name: str, required_columns: Optional[Set[str]] = None) -> None:
    """Проверяет данные на валидность"""
    if df.empty:
        raise ValueError(f"Лист '{sheet_name}' пуст!")

    if df.isnull().values.any():
        logger.warning(f"Обнаружены пропущенные значения в листе '{sheet_name}'")

    if required_columns:
        missing_cols = required_columns - set(df.columns)
        if missing_cols:
            raise ValueError(f"В листе '{sheet_name}' отсутствуют колонки: {missing_cols}")


def clean_data(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    """Обрабатывает пропущенные значения"""
    if df.isnull().values.any():
        logger.info(f"Очистка данных в листе '{sheet_name}'")

        num_cols = df.select_dtypes(include='number').columns
        df[num_cols] = df[num_cols].fillna(0)

        cat_cols = df.select_dtypes(exclude='number').columns
        df[cat_cols] = df[cat_cols].fillna('Unknown')

        if 'method_in_dwh' in df.columns:
            df['method_in_dwh'] = df['method_in_dwh'].fillna('unknown_method')

    return df
