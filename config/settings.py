import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class Settings:
    INPUT_FILE = os.path.join(BASE_DIR, "raw/input.xlsx")
    OUTPUT_EXCEL = os.path.join(BASE_DIR, "results/output.xlsx")
    OUTPUT_PLOT = os.path.join(BASE_DIR, "results/plot.png")

settings = Settings()
