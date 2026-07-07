import sqlite3
import pandas as pd
from pathlib import Path

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = r"data/raw/Indian_Food_Nutrition_Processed.csv"
DB_PATH = r"data/processed/nutrition.db"

# =========================
# SQLITE SCHEMA
# =========================
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dish_name TEXT NOT NULL,
    calories REAL,
    carbs REAL,
    protein REAL,
    fats REAL,
    free_sugar REAL,
    fibre REAL,
    sodium REAL,
    calcium REAL,
    iron REAL,
    vitamin_c REAL,
    folate REAL
);
"""

# =========================
# LOAD & CLEAN CSV
# =========================
def load_and_clean_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    # ---- RENAME COLUMNS (EXACT MATCH) ----
    df = df.rename(columns={
        "Dish Name": "dish_name",
        "Calories (kcal)": "calories",
        "Carbohydrates (g)": "carbs",
        "Protein (g)": "protein",
        "Fats (g)": "fats",
        "Free Sugar (g)": "free_sugar",
        "Fibre (g)": "fibre",
        "Sodium (mg)": "sodium",
        "Calcium (mg)": "calcium",
        "Iron (mg)": "iron",
        "Vitamin C (mg)": "vitamin_c",
        "Folate (µg)": "folate"
    })

    required_columns = [
        "dish_name", "calories", "carbs", "protein", "fats",
        "free_sugar", "fibre", "sodium", "calcium",
        "iron", "vitamin_c", "folate"
    ]

    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"❌ Missing columns in CSV: {missing}")

    # ---- NUMERIC CONVERSION ----
    numeric_cols = required_columns[1:]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ---- HANDLE MISSING VALUES ----
    df[numeric_cols] = df[numeric_cols].fillna(0)
    df["dish_name"] = df["dish_name"].astype(str).str.strip()

    return df[required_columns]

# =========================
# LOAD INTO SQLITE
# =========================
def load_to_sqlite(df: pd.DataFrame, db_path: Path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(CREATE_TABLE_SQL)

    df.to_sql(
        "foods",
        conn,
        if_exists="append",
        index=False
    )

    # ---- INDEXES FOR FAST AGENT QUERIES ----
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dish_name ON foods(dish_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_calories ON foods(calories)")

    conn.commit()
    conn.close()

# =========================
# MAIN
# =========================
def main():
    print("📥 Reading CSV:", CSV_PATH)
    df = load_and_clean_csv(CSV_PATH)

    print(f"✅ Rows loaded: {len(df)}")
    load_to_sqlite(df, DB_PATH)

    print("🎉 SQLite nutrition database ready!")
    print("📦 DB path:", DB_PATH)

if __name__ == "__main__":
    main()
