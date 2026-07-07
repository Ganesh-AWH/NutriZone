import sqlite3
from pathlib import Path
from typing import List, Dict, Optional

# =========================
# DATABASE PATH
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "processed" / "nutrition.db"


# =========================
# CONNECTION HELPER
# =========================
def get_connection():
    return sqlite3.connect(DB_PATH)


# =========================
# BASIC QUERIES
# =========================
def get_food_count() -> int:
    """Return total number of food items"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM foods")
    count = cursor.fetchone()[0]

    conn.close()
    return count


def get_food_by_name(dish_name: str) -> Optional[Dict]:
    """Fetch full nutrition data for a single dish"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM foods
        WHERE dish_name = ?
        """,
        (dish_name,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    columns = [
        "id", "dish_name", "calories", "carbs", "protein", "fats",
        "free_sugar", "fibre", "sodium", "calcium",
        "iron", "vitamin_c", "folate"
    ]

    return dict(zip(columns, row))


# =========================
# FILTER QUERIES (AGENT CORE)
# =========================
def get_foods_by_calories(
    max_calories: float,
    limit: int = 20
) -> List[Dict]:
    """Foods under a calorie limit"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT dish_name, calories, protein, carbs, fats
        FROM foods
        WHERE calories <= ?
        ORDER BY calories ASC
        LIMIT ?
        """,
        (max_calories, limit)
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "dish_name": r[0],
            "calories": r[1],
            "protein": r[2],
            "carbs": r[3],
            "fats": r[4],
        }
        for r in rows
    ]


def get_high_protein_foods(
    min_protein: float,
    max_calories: Optional[float] = None,
    limit: int = 20
) -> List[Dict]:
    """High protein foods with optional calorie cap"""
    conn = get_connection()
    cursor = conn.cursor()

    if max_calories:
        cursor.execute(
            """
            SELECT dish_name, protein, calories
            FROM foods
            WHERE protein >= ?
              AND calories <= ?
            ORDER BY protein DESC
            LIMIT ?
            """,
            (min_protein, max_calories, limit)
        )
    else:
        cursor.execute(
            """
            SELECT dish_name, protein, calories
            FROM foods
            WHERE protein >= ?
            ORDER BY protein DESC
            LIMIT ?
            """,
            (min_protein, limit)
        )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "dish_name": r[0],
            "protein": r[1],
            "calories": r[2],
        }
        for r in rows
    ]

def get_high_protein_foods_full(
    min_protein: float,
    max_calories: float = None,
    limit: int = 20
):
    conn = get_connection()
    cursor = conn.cursor()

    if max_calories:
        cursor.execute(
            """
            SELECT *
            FROM foods
            WHERE protein >= ?
              AND calories <= ?
            ORDER BY protein DESC
            LIMIT ?
            """,
            (min_protein, max_calories, limit)
        )
    else:
        cursor.execute(
            """
            SELECT *
            FROM foods
            WHERE protein >= ?
            ORDER BY protein DESC
            LIMIT ?
            """,
            (min_protein, limit)
        )

    rows = cursor.fetchall()
    conn.close()

    columns = [
        "id", "dish_name", "calories", "carbs", "protein", "fats",
        "free_sugar", "fibre", "sodium", "calcium",
        "iron", "vitamin_c", "folate"
    ]

    return [dict(zip(columns, r)) for r in rows]


def get_low_sugar_foods(
    max_sugar: float,
    limit: int = 20
) -> List[Dict]:
    """Low free-sugar foods (diabetic-safe filter)"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT dish_name, free_sugar, calories
        FROM foods
        WHERE free_sugar <= ?
        ORDER BY free_sugar ASC
        LIMIT ?
        """,
        (max_sugar, limit)
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "dish_name": r[0],
            "free_sugar": r[1],
            "calories": r[2],
        }
        for r in rows
    ]


def get_high_fibre_foods(
    min_fibre: float,
    limit: int = 20
) -> List[Dict]:
    """High fibre foods (satiety & gut health)"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT dish_name, fibre, calories
        FROM foods
        WHERE fibre >= ?
        ORDER BY fibre DESC
        LIMIT ?
        """,
        (min_fibre, limit)
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "dish_name": r[0],
            "fibre": r[1],
            "calories": r[2],
        }
        for r in rows
    ]
