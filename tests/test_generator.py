# Tests of data generator (every test works on temporary copy of original db)

import hashlib
import random
import sqlite3

import pandas as pd
import pytest

from config import (
    BEST_PERFORMANCE,
    CLEAN_DATA,
    DB_PATH,
    ERR_BAD_DATE,
    ERR_FAKE_NULL,
    ERR_INCONSISTENT,
    ERR_NULL,
    ERR_OUT_OF_RANGE,
    ERROR_TYPES,
    MIN_SALE,
    RAW_DATA,
    TOTAL_SALES,
    WORST_PERFORMANCE,
)
from src.db import set_db_path
from src.queries import (
    get_client_data_sales_across_years,
    get_top_perfromance_categories,
    get_top_perfromance_customers,
    get_top_perfromance_products,
    get_years_filter_from_data,
)
from src.generator import (
    COUNTRIES,
    ensure_mutable_db,
    generate_customers,
    generate_orders,
    generate_products,
    get_dirty_value,
    get_errors_log,
    get_errors_per_year,
    get_next_id_number,
    get_runs_log,
    get_tables_counts,
)
from src.transform import get_mapped_categories_df, get_mapped_countries_df


@pytest.fixture
def db(tmp_path):
    db_path=str(tmp_path/"db_shop_mutable.db")
    ensure_mutable_db(DB_PATH, db_path)
    return db_path


def rng():
    return random.Random(42)


def query(db_path, sql):
    with sqlite3.connect(db_path) as conn:
        return conn.execute(sql).fetchall()


def file_hash(path):
    with open(path, "rb") as file:
        return hashlib.md5(file.read()).hexdigest()


### Mutable db

def test_mutable_db_is_copy_of_original(db):
    assert file_hash(db)==file_hash(DB_PATH)


def test_mutable_db_is_not_overwritten_when_exists(db):
    generate_customers(db, 3, 0, ERROR_TYPES, rng())
    hash_before=file_hash(db)

    ensure_mutable_db(DB_PATH, db)

    assert file_hash(db)==hash_before


def test_original_db_is_never_changed(db):
    hash_before=file_hash(DB_PATH)

    generate_customers(db, 5, 0.5, ERROR_TYPES, rng())
    generate_products(db, 5, 0.5, ERROR_TYPES, rng())
    generate_orders(db, 5, 0.5, ERROR_TYPES, rng())

    assert file_hash(DB_PATH)==hash_before


### Ids

def test_next_id_number(db):
    with sqlite3.connect(db) as conn:
        assert get_next_id_number(conn, "Customers", "CustomerID", "C")==60
        assert get_next_id_number(conn, "Products", "ProductID", "P")==51


def test_generated_ids_continue_numbering(db):
    generate_customers(db, 2, 0, ERROR_TYPES, rng())
    generate_products(db, 1, 0, ERROR_TYPES, rng())

    assert query(db, "SELECT CustomerID FROM Customers WHERE CustomerID>'C059' ORDER BY 1")==[("C060",), ("C061",)]
    assert query(db, "SELECT ProductID FROM Products WHERE ProductID>'P050'")==[("P051",)]


def test_generating_twice_appends_records(db):
    generate_customers(db, 3, 0, ERROR_TYPES, rng())
    generate_customers(db, 4, 0, ERROR_TYPES, rng())

    assert query(db, "SELECT count(*) FROM Customers")==[(59+7,)]
    assert query(db, "SELECT count(DISTINCT CustomerID) FROM Customers")==[(59+7,)]


### Clean records (pollution 0%)

def test_no_pollution_gives_no_errors(db):
    generate_customers(db, 10, 0, ERROR_TYPES, rng())
    generate_products(db, 10, 0, ERROR_TYPES, rng())
    result=generate_orders(db, 10, 0, ERROR_TYPES, rng())

    assert result["polluted"]==0
    assert get_errors_log(db).empty


def test_clean_customers_have_correct_country(db):
    generate_customers(db, 20, 0, ERROR_TYPES, rng())

    countries=query(db, "SELECT DISTINCT Country FROM Customers WHERE CustomerID>'C059'")

    assert {country for (country,) in countries}<=set(COUNTRIES)


def test_clean_orders_have_valid_dates_and_values(db):
    generate_orders(db, 20, 0, ERROR_TYPES, rng())

    assert query(db, "SELECT count(*) FROM Orders WHERE OrderID>'O4141' AND strftime('%Y', OrderDate) IS NULL")==[(0,)]
    assert query(db, '''
        SELECT count(*) FROM OrderDetails
        WHERE OrderDetailID>'OD4184' AND (Quantity<=0 OR UnitPrice IS NULL OR UnitPrice<=0)
    ''')==[(0,)]


def test_orders_reference_existing_records(db):
    generate_orders(db, 30, 0.5, ERROR_TYPES, rng())

    assert query(db, '''
        SELECT count(*) FROM Orders o LEFT JOIN Customers c ON c.CustomerID=o.CustomerID WHERE c.CustomerID IS NULL
    ''')==[(0,)]
    assert query(db, '''
        SELECT count(*) FROM OrderDetails od LEFT JOIN Orders o ON o.OrderID=od.OrderID WHERE o.OrderID IS NULL
    ''')==[(0,)]
    assert query(db, '''
        SELECT count(*) FROM OrderDetails od LEFT JOIN Products p ON p.ProductID=od.ProductID WHERE p.ProductID IS NULL
    ''')==[(0,)]


def test_orders_need_customers_and_products(db):
    with sqlite3.connect(db) as conn:
        conn.execute("DELETE FROM Customers")

    with pytest.raises(ValueError, match="Generate customers and products first"):
        generate_orders(db, 5, 0, ERROR_TYPES, rng())

    assert query(db, "SELECT count(*) FROM Orders")==[(186,)]


### Polluted records

def test_full_pollution_pollutes_every_record(db):
    result=generate_customers(db, 10, 1, ERROR_TYPES, rng())

    assert result["polluted"]==10
    assert len(get_errors_log(db))==10


def test_only_chosen_error_types_are_inserted(db):
    generate_orders(db, 30, 1, [ERR_BAD_DATE], rng())

    df_errors=get_errors_log(db)

    assert set(df_errors["ErrorType"])=={ERR_BAD_DATE}
    assert set(df_errors["ColumnName"])=={"OrderDate"}


def test_error_type_that_does_not_fit_table_inserts_nothing(db):
    # Out of range values are only in OrderDetails
    result=generate_customers(db, 10, 1, [ERR_OUT_OF_RANGE], rng())

    assert result["polluted"]==0


def test_log_has_true_and_dirty_value_like_in_db(db):
    generate_customers(db, 10, 1, [ERR_INCONSISTENT], rng())

    for _, error in get_errors_log(db).iterrows():
        (country,)=query(db, f"SELECT Country FROM Customers WHERE CustomerID='{error['RecordID']}'")[0]

        assert country==error["DirtyValue"]
        assert error["TrueValue"] in COUNTRIES


def test_tables_counts(db):
    generate_products(db, 4, 0, ERROR_TYPES, rng())

    df=get_tables_counts(db).set_index("Table")["Rows"]

    assert df["Products"]==54
    assert df["Customers"]==59


### Year of data delivery and runs log

def test_orders_are_in_year_of_data_delivery(db):
    generate_orders(db, 30, 0, ERROR_TYPES, rng(), load_year=2023)

    years=query(db, "SELECT DISTINCT strftime('%Y', OrderDate) FROM Orders WHERE OrderID>'O4141'")

    assert years==[("2023",)]


def test_orders_are_not_before_registration(db):
    generate_customers(db, 10, 0, ERROR_TYPES, rng(), load_year=2024)
    generate_orders(db, 50, 0, ERROR_TYPES, rng(), load_year=2024)

    assert query(db, '''
        SELECT count(*) FROM Orders o INNER JOIN Customers c ON c.CustomerID=o.CustomerID
        WHERE o.OrderID>'O4141' AND o.OrderDate<c.RegistrationDate
    ''')==[(0,)]


def test_customers_are_registered_in_year_of_data_delivery(db):
    generate_customers(db, 10, 0, ERROR_TYPES, rng(), load_year=2022)

    assert query(db, "SELECT DISTINCT strftime('%Y', RegistrationDate) FROM Customers WHERE CustomerID>'C059'")==[("2022",)]


def test_orders_need_customers_registered_before_end_of_year(db):
    with pytest.raises(ValueError, match="No customers registered before end of 2021"):
        generate_orders(db, 5, 0, ERROR_TYPES, rng(), load_year=2021)


def test_every_run_is_saved_even_without_errors(db):
    first=generate_customers(db, 3, 0, ERROR_TYPES, rng(), load_year=2023)
    second=generate_orders(db, 4, 0.5, ERROR_TYPES, rng(), load_year=2024)

    df_runs=get_runs_log(db).set_index("RunID")

    assert second["run_id"]==first["run_id"]+1
    assert df_runs.loc[first["run_id"], "PollutedRows"]==0
    assert df_runs.loc[second["run_id"], "LoadYear"]==2024
    assert df_runs.loc[second["run_id"], "PollutionLevel"]==0.5
    # Orders run has rows of orders and order details
    assert df_runs.loc[second["run_id"], "InsertedRows"]==second["inserted"]+second["inserted_details"]


def test_errors_have_run_year_and_pollution_level(db):
    result=generate_customers(db, 5, 1, ERROR_TYPES, rng(), load_year=2022)

    df_errors=get_errors_log(db)

    assert set(df_errors["RunID"])=={result["run_id"]}
    assert set(df_errors["LoadYear"])=={2022}
    assert set(df_errors["PollutionLevel"])=={1.0}


def test_errors_per_year():
    df_runs=pd.DataFrame({
        "LoadYear":[2023, 2023, 2024, None],
        "InsertedRows":[10, 10, 50, 5],
        "PollutedRows":[1, 1, 20, 5],
    })

    df_years=get_errors_per_year(df_runs)

    assert df_years.to_dict("records")==[
        {"LoadYear":2023, "InsertedRows":20, "PollutedRows":2, "PollutedPercent":10.0},
        {"LoadYear":2024, "InsertedRows":50, "PollutedRows":20, "PollutedPercent":40.0},
    ]


def test_errors_per_year_without_runs(db):
    # First opening of generator: no runs yet
    df_years=get_errors_per_year(get_runs_log(db))

    assert df_years.empty
    assert "PollutedPercent" in df_years.columns


def test_old_errors_table_gets_new_columns(db):
    # First version of the table, before RunID, LoadYear and PollutionLevel
    with sqlite3.connect(db) as conn:
        conn.execute('''
            CREATE TABLE Data_Quality_Errors (
                ErrorID INTEGER PRIMARY KEY AUTOINCREMENT, TableName TEXT, RecordID TEXT, ColumnName TEXT,
                TrueValue TEXT, DirtyValue TEXT, ErrorType TEXT, CreatedAt TEXT
            )
        ''')
        conn.execute("INSERT INTO Data_Quality_Errors (TableName, RecordID) VALUES ('Customers', 'C001')")

    assert get_errors_log(db)["RunID"].isna().all()

    generate_customers(db, 3, 1, ERROR_TYPES, rng(), load_year=2025)

    df_errors=get_errors_log(db)
    assert len(df_errors)==4
    assert df_errors["LoadYear"].tolist().count(2025)==3


def test_reading_logs_does_not_change_original_db():
    hash_before=file_hash(DB_PATH)

    assert get_errors_log(DB_PATH).empty
    assert get_runs_log(DB_PATH).empty
    assert file_hash(DB_PATH)==hash_before


### App connected to mutable db: clean data does not show inserted errors

@pytest.fixture
def connected_db(db):
    # App queries use tmp mutable db, after test original db again
    set_db_path(db)
    yield db
    set_db_path(DB_PATH)


def test_clean_data_has_no_values_out_of_range(connected_db):
    generate_orders(connected_db, 40, 1, [ERR_OUT_OF_RANGE], rng())
    years=get_years_filter_from_data(CLEAN_DATA)

    for get_top in [get_top_perfromance_products, get_top_perfromance_categories]:
        df_clean=get_top(WORST_PERFORMANCE, years, MIN_SALE, CLEAN_DATA)
        df_raw=get_top(WORST_PERFORMANCE, years, MIN_SALE, RAW_DATA)

        assert (df_clean["TotalSales"]>0).all(), get_top.__name__
        assert (df_raw["TotalSales"]<=0).any(), get_top.__name__


@pytest.mark.parametrize("data_version", [CLEAN_DATA, RAW_DATA])
def test_top_performance_sums_only_chosen_year(connected_db, data_version):
    # Customer with orders in 2 years: sales of 2023 can not have orders of 2024
    with sqlite3.connect(connected_db) as conn:
        conn.execute("INSERT INTO Customers VALUES ('C900', 'Test', 'Client', 't@example.com', 'Poland', '2022-01-01')")
        conn.execute("INSERT INTO Orders VALUES ('O9001', 'C900', '2023-05-05', 0)")
        conn.execute("INSERT INTO Orders VALUES ('O9002', 'C900', '2024-05-05', 0)")
        conn.execute("INSERT INTO OrderDetails VALUES ('OD9001', 'O9001', 'P001', 1, 100000.0)")
        conn.execute("INSERT INTO OrderDetails VALUES ('OD9002', 'O9002', 'P001', 1, 200000.0)")

    for year, expected in [("2023", 100000.0), ("2024", 200000.0)]:
        df=get_top_perfromance_customers(BEST_PERFORMANCE, [year], TOTAL_SALES, data_version)
        sales=df.set_index("FullName")["TotalSales"]

        assert sales["Test Client"]==expected, year


def test_clean_categories_have_no_empty_category(connected_db):
    generate_products(connected_db, 20, 1, [ERR_NULL, ERR_FAKE_NULL], rng())
    # Orders with every product, so polluted products have sales
    with sqlite3.connect(connected_db) as conn:
        products=[row[0] for row in conn.execute("SELECT ProductID FROM Products WHERE ProductID>'P050'")]
        conn.execute("INSERT INTO Orders VALUES ('O9001', 'C001', '2024-05-05', 0)")
        conn.executemany("INSERT INTO OrderDetails VALUES (?, 'O9001', ?, 1, 100.0)", [(f"OD9{i:03d}", p) for i, p in enumerate(products)])

    years=get_years_filter_from_data(CLEAN_DATA)
    df_clean=get_top_perfromance_categories(WORST_PERFORMANCE, years, TOTAL_SALES, CLEAN_DATA)
    df_raw=get_top_perfromance_categories(WORST_PERFORMANCE, years, TOTAL_SALES, RAW_DATA)

    assert set(df_clean["Category_Fixed"])=={"Audio", "Electronics", "Photo", "Tablets", "Wearables"}
    assert df_clean["RankedCategorysBySales"].tolist()==[1, 2, 3, 4, 5]
    # Raw data still shows empty categories
    raw_categories=df_raw["Category_Fixed"]
    assert raw_categories.isna().any() or raw_categories.astype(str).str.strip().str.lower().isin(["", "null", "none"]).any()


def test_clean_data_has_no_impossible_dates(connected_db):
    generate_orders(connected_db, 40, 1, [ERR_BAD_DATE], rng())
    customer_ids=[row[0] for row in query(connected_db, "SELECT CustomerID FROM Orders WHERE OrderID>'O4141'")]
    clients=[row[0] for row in query(connected_db, f'''
        SELECT DISTINCT FirstName || ' ' || LastName FROM Customers WHERE CustomerID IN ({",".join(f"'{c}'" for c in customer_ids)})
    ''')]

    years=get_years_filter_from_data(CLEAN_DATA)
    assert None not in years

    for client in clients:
        df=get_client_data_sales_across_years(years, client, CLEAN_DATA)
        assert df["OrderYear"].notna().all(), client


### Dirty values: cleaning has to recover true value (or remove the record)

@pytest.mark.parametrize("true_country", COUNTRIES)
def test_inconsistent_country_is_recovered_by_cleaning(true_country):
    for seed in range(20):
        dirty=get_dirty_value(random.Random(seed), "Country", true_country, ERR_INCONSISTENT)
        df=get_mapped_countries_df(pd.DataFrame({"Country":[dirty]}), CLEAN_DATA)

        assert dirty!=true_country
        assert df["Country_mapped"].iloc[0]==true_country


@pytest.mark.parametrize("true_category", ["Audio", "Electronics", "Photo", "Tablets", "Wearables"])
def test_inconsistent_category_is_recovered_by_cleaning(true_category):
    for seed in range(20):
        dirty=get_dirty_value(random.Random(seed), "Category", true_category, ERR_INCONSISTENT)
        df=get_mapped_categories_df(pd.DataFrame({"Category":[dirty]}))

        assert dirty!=true_category
        assert df["Category_mapped"].iloc[0]==true_category


def test_bad_date_gives_no_year_in_sqlite():
    for seed in range(20):
        dirty=get_dirty_value(random.Random(seed), "OrderDate", "2024-06-15", ERR_BAD_DATE)

        assert query(":memory:", f"SELECT strftime('%Y', '{dirty}')")==[(None,)]


@pytest.mark.parametrize("column, true_value", [("Quantity", 2), ("UnitPrice", 299.9)])
def test_out_of_range_value(column, true_value):
    for seed in range(20):
        assert get_dirty_value(random.Random(seed), column, true_value, ERR_OUT_OF_RANGE)<=0


def test_null_and_fake_null():
    assert get_dirty_value(rng(), "Country", "Poland", ERR_NULL) is None
    assert get_dirty_value(rng(), "Country", "Poland", ERR_FAKE_NULL).strip().lower() in {"", "null", "none"}
