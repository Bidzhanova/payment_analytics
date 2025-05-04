import os

# Пути относительно корня проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FILE = os.path.join(BASE_DIR, 'data/raw/test_data.xlsx')
OUTPUT_EXCEL = os.path.join(BASE_DIR, 'data/processed/analysis.xlsx')
OUTPUT_PLOT = os.path.join(BASE_DIR, 'data/results/plots/combined_plot.png')

# Настройки графиков
PLOT_SETTINGS = {
    'style': 'seaborn-v0_8',
    'size': (16, 12),
    'palette': 'viridis',
    'dpi': 150
}
