# Static variables used in the whole app

import os

from src.generator_config import ERR_BAD_DATE, ERR_FAKE_NULL, ERR_INCONSISTENT, ERR_NULL, ERR_OUT_OF_RANGE

# Path to db works no matter from which folder app is started
DATA_DIR=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Original db is never changed, generator inserts records only to mutable db (copy of original)
DB_PATH=os.path.join(DATA_DIR, "db_shop.db")
MUTABLE_DB_PATH=os.path.join(DATA_DIR, "db_shop_mutable.db")

DB_ORIGINAL="📁 Original DB"
DB_MUTABLE="🧪 Mutable DB"

CUSTOMER_SEC="Check specyfic client"
PRODUCTS_SEC="Check products "

MODE_TOP="🥇Top Performance"
MODE_CLIENT="🔍 Deep Dive: Client"
# PRDUCT_INSIGHTS="📦 Product Insights"
MODE_GENERATOR="🧪 Data Generator"

BEST_PERFORMANCE="BEST 📈"
WORST_PERFORMANCE="WORST 📉"

AVG_SALES = "📊 Average Sales"
TOTAL_SALES = "💰 Total Sales"
MAX_SALE = "🏆 Maximum Sale"
MIN_SALE = "📉 Minimum Sale"

RAW_DATA="🗃️ Raw data"
CLEAN_DATA="🧹 Clean data"

ALL_YEARS="All of the years"

# Types of errors that generator can insert into data (names of errors are in src/generator_config.py)
ERROR_TYPES=[ERR_NULL, ERR_FAKE_NULL, ERR_INCONSISTENT, ERR_OUT_OF_RANGE, ERR_BAD_DATE]

# Years of data delivery that generator can simulate
LOAD_YEARS=[2022, 2023, 2024, 2025]
