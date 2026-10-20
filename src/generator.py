# Data generator: inserting new (clean or polluted) records into mutable db
# Every polluted value is saved in Data_Quality_Errors with its true value

import os
import random
import shutil
import sqlite3
from datetime import date, datetime, timedelta

import pandas as pd

from config import ERR_BAD_DATE, ERR_FAKE_NULL, ERR_INCONSISTENT, ERR_NULL, ERR_OUT_OF_RANGE
from src.transform import CATEGORIES_DICT, COUNTRIES_DICT


#### DATA TO GENERATE CLEAN RECORDS

START_DATE=date(2022, 1, 1)
END_DATE=date(2025, 12, 31)

FIRST_NAMES=["Anna", "Piotr", "Marta", "Jan", "Ewa", "Tomasz", "Karolina", "Kamil", "Natalia", "Adam",
             "John", "Jane", "Hans", "Marie", "Luis", "Zhang", "Ola", "Michał", "Zofia", "Paweł"]
LAST_NAMES=["Nowak", "Kowalski", "Zielińska", "Kowal", "Lewandowski", "Wiśniewska", "Mazur", "Kaczmarek",
            "Smith", "Doe", "Müller", "Dubois", "García", "Wei", "Wójcik", "Kamińska", "Szymański"]

# Correct names (the same as clean data gives)
COUNTRIES=sorted(set(COUNTRIES_DICT.values()))
CATEGORIES=sorted(set(CATEGORIES_DICT.values()))

# Product names and price range like in original db
PRODUCTS_BY_CATEGORY={
    "Electronics":(["Laptop 13\"", "Laptop 14\"", "Laptop 15\"", "Smartphone X", "Smartphone Y", "Smartphone Z", "Monitor 24\"", "Monitor 27\""], 1099, 4199),
    "Audio":(["Headphones", "Earbuds", "Speaker", "Speaker Max"], 199.9, 599),
    "Photo":(["Camera", "Camera Pro"], 1999, 2499),
    "Tablets":(["Tablet Mini", "Tablet Pro"], 2299, 2499),
    "Wearables":(["Smart Watch"], 899, 899),
}

# Which error types can be inserted into which column
POLLUTABLE_COLUMNS={
    "Customers":{"Country":[ERR_NULL, ERR_FAKE_NULL, ERR_INCONSISTENT]},
    "Products":{"Category":[ERR_NULL, ERR_FAKE_NULL, ERR_INCONSISTENT]},
    "Orders":{"OrderDate":[ERR_NULL, ERR_FAKE_NULL, ERR_BAD_DATE]},
    "OrderDetails":{"Quantity":[ERR_OUT_OF_RANGE], "UnitPrice":[ERR_NULL, ERR_OUT_OF_RANGE]},
}

FAKE_NULLS=["null", "NULL", "None", "none", "", " "]


#### MUTABLE DB

# Function to create mutable db as copy of original (only if it does not exist)
def ensure_mutable_db(original_path, mutable_path):

    if not os.path.exists(mutable_path):
        shutil.copyfile(original_path, mutable_path)


# Function to create tables with log of generator runs and inserted errors
def create_quality_tables(conn):

    # One row = one click of generator (one chunk of data delivered in LoadYear)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Generator_Runs (
            RunID INTEGER PRIMARY KEY AUTOINCREMENT,
            TableName TEXT,
            LoadYear INTEGER,
            PollutionLevel REAL,
            InsertedRows INTEGER,
            PollutedRows INTEGER,
            CreatedAt TEXT
        )
    ''')

    # One row = one polluted value
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Data_Quality_Errors (
            ErrorID INTEGER PRIMARY KEY AUTOINCREMENT,
            RunID INTEGER,
            TableName TEXT,
            RecordID TEXT,
            ColumnName TEXT,
            TrueValue TEXT,
            DirtyValue TEXT,
            ErrorType TEXT,
            LoadYear INTEGER,
            PollutionLevel REAL,
            CreatedAt TEXT
        )
    ''')

    # First version of the table had no RunID, LoadYear and PollutionLevel
    existing_columns={row[1] for row in conn.execute("PRAGMA table_info(Data_Quality_Errors)")}
    for column, column_type in [("RunID","INTEGER"), ("LoadYear","INTEGER"), ("PollutionLevel","REAL")]:
        if column not in existing_columns:
            conn.execute(f"ALTER TABLE Data_Quality_Errors ADD COLUMN {column} {column_type}")


# Function to get next number of id, e.g. C059 -> 60
def get_next_id_number(conn, table, id_col, prefix):

    ids=[row[0] for row in conn.execute(f"SELECT {id_col} FROM {table}")]
    numbers=[int(i[len(prefix):]) for i in ids if i and i.startswith(prefix) and i[len(prefix):].isdigit()]

    return max(numbers, default=0)+1


#### POLLUTING DATA

def get_random_date(rng, start=START_DATE, end=END_DATE):

    return start+timedelta(days=rng.randint(0, (end-start).days))


# Function to get range of dates for chunk of data (whole range if year is not chosen)
def get_dates_range(load_year):

    if load_year is None:
        return START_DATE, END_DATE

    return date(load_year, 1, 1), date(load_year, 12, 31)


# Function to get spelling of the value that cleaning still maps to the true value
def get_inconsistent_value(rng, column, true_value):

    if column=="Country":
        variants=[key for key, val in COUNTRIES_DICT.items() if val==true_value]
    else:
        variants=[true_value]

    variant=rng.choice(variants)
    for _ in range(10):
        dirty=rng.choice([variant.upper(), variant.lower(), variant.title(), f" {variant} "])
        if dirty!=true_value:
            return dirty

    return f" {true_value.upper()} "


# Function to get dirty value of the column for the error type
def get_dirty_value(rng, column, true_value, error_type):

    if error_type==ERR_NULL:
        return None

    if error_type==ERR_FAKE_NULL:
        return rng.choice(FAKE_NULLS)

    if error_type==ERR_INCONSISTENT:
        return get_inconsistent_value(rng, column, true_value)

    if error_type==ERR_OUT_OF_RANGE:
        if column=="Quantity":
            return rng.choice([0, -1, -rng.randint(2, 5)])
        return -abs(true_value)

    if error_type==ERR_BAD_DATE:
        year, month, day=true_value.split("-")
        # Day 32-34 or month 13, SQLite strftime gives NULL for both
        if rng.random()<0.5:
            return f"{year}-{month}-{rng.randint(32, 34)}"
        return f"{year}-13-{day}"

    raise ValueError(f"Unknown error type: {error_type}")


def to_text(value):
    return None if value is None else str(value)


# Function to pollute one record (with probability = pollution), error is saved to log
def pollute_record(rng, table, record_id, record, pollution, error_types, errors_log):

    if rng.random()>=pollution:
        return record

    options=[
        (column, error_type)
        for column, column_errors in POLLUTABLE_COLUMNS[table].items()
        for error_type in column_errors
        if error_type in error_types
    ]

    # None of chosen error types can be used in this table
    if not options:
        return record

    column, error_type=rng.choice(options)
    dirty_value=get_dirty_value(rng, column, record[column], error_type)

    errors_log.append((table, record_id, column, to_text(record[column]), to_text(dirty_value), error_type))
    record[column]=dirty_value

    return record


# Function to save run of generator and log of its errors to db, returns RunID
def save_run(conn, table, load_year, pollution, inserted_rows, errors_log):

    created_at=datetime.now().isoformat(timespec="seconds")

    cursor=conn.execute('''
        INSERT INTO Generator_Runs (TableName, LoadYear, PollutionLevel, InsertedRows, PollutedRows, CreatedAt)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (table, load_year, pollution, inserted_rows, len(errors_log), created_at))
    run_id=cursor.lastrowid

    conn.executemany('''
        INSERT INTO Data_Quality_Errors (RunID, TableName, RecordID, ColumnName, TrueValue, DirtyValue, ErrorType, LoadYear, PollutionLevel, CreatedAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [(run_id,)+error+(load_year, pollution, created_at) for error in errors_log])

    return run_id


#### GENERATORS

# Function to insert new customers (registered in load_year)
def generate_customers(db_path, n, pollution, error_types, rng=None, load_year=None):

    rng=rng or random.Random()
    errors_log=[]

    # Without chosen year registration until middle of 2025, so there is time for orders after it
    start, end=get_dates_range(load_year) if load_year else (START_DATE, date(2025, 6, 30))

    with sqlite3.connect(db_path) as conn:
        create_quality_tables(conn)
        next_number=get_next_id_number(conn, "Customers", "CustomerID", "C")

        rows=[]
        for i in range(n):
            customer_id=f"C{next_number+i:03d}"
            first_name=rng.choice(FIRST_NAMES)
            last_name=rng.choice(LAST_NAMES)

            record={
                "CustomerID":customer_id,
                "FirstName":first_name,
                "LastName":last_name,
                "Email":f"{first_name}.{last_name}@example.com".lower(),
                "Country":rng.choice(COUNTRIES),
                "RegistrationDate":get_random_date(rng, start, end).isoformat(),
            }
            record=pollute_record(rng, "Customers", customer_id, record, pollution, error_types, errors_log)
            rows.append(record)

        conn.executemany('''
            INSERT INTO Customers (CustomerID, FirstName, LastName, Email, Country, RegistrationDate)
            VALUES (:CustomerID, :FirstName, :LastName, :Email, :Country, :RegistrationDate)
        ''', rows)
        run_id=save_run(conn, "Customers", load_year, pollution, len(rows), errors_log)

    return {"run_id":run_id, "inserted":len(rows), "polluted":len(errors_log)}


# Function to insert new products (products have no date, load_year is only saved in log)
def generate_products(db_path, n, pollution, error_types, rng=None, load_year=None):

    rng=rng or random.Random()
    errors_log=[]

    with sqlite3.connect(db_path) as conn:
        create_quality_tables(conn)
        next_number=get_next_id_number(conn, "Products", "ProductID", "P")

        rows=[]
        for i in range(n):
            product_id=f"P{next_number+i:03d}"
            category=rng.choice(CATEGORIES)
            names, min_price, max_price=PRODUCTS_BY_CATEGORY[category]

            record={
                "ProductID":product_id,
                "ProductName":rng.choice(names),
                "Category":category,
                "Price":round(rng.uniform(min_price, max_price), 2),
                "StockQuantity":rng.randint(0, 200),
            }
            record=pollute_record(rng, "Products", product_id, record, pollution, error_types, errors_log)
            rows.append(record)

        conn.executemany('''
            INSERT INTO Products (ProductID, ProductName, Category, Price, StockQuantity)
            VALUES (:ProductID, :ProductName, :Category, :Price, :StockQuantity)
        ''', rows)
        run_id=save_run(conn, "Products", load_year, pollution, len(rows), errors_log)

    return {"run_id":run_id, "inserted":len(rows), "polluted":len(errors_log)}


# Function to get date of registration (wrong date is treated as registration at start)
def get_registration_date(registration_date):

    try:
        return date.fromisoformat(registration_date)
    except (TypeError, ValueError):
        return START_DATE


# Function to insert new orders with order details in load_year (customers and products have to exist)
def generate_orders(db_path, n, pollution, error_types, rng=None, load_year=None):

    rng=rng or random.Random()
    errors_log=[]
    year_start, year_end=get_dates_range(load_year)

    with sqlite3.connect(db_path) as conn:
        create_quality_tables(conn)

        customers=conn.execute("SELECT CustomerID, RegistrationDate FROM Customers").fetchall()
        products=conn.execute("SELECT ProductID, Price FROM Products").fetchall()

        if not customers or not products:
            raise ValueError("Orders need existing customers and products. Generate customers and products first.")

        # Order can not be before registration of the customer
        customers=[
            (customer_id, max(get_registration_date(registration_date), year_start))
            for customer_id, registration_date in customers
            if get_registration_date(registration_date)<=year_end
        ]

        if not customers:
            raise ValueError(f"No customers registered before end of {load_year}. Generate customers for this year first.")

        next_order=get_next_id_number(conn, "Orders", "OrderID", "O")
        next_detail=get_next_id_number(conn, "OrderDetails", "OrderDetailID", "OD")

        orders=[]
        details=[]
        for i in range(n):
            order_id=f"O{next_order+i}"
            customer_id, start=rng.choice(customers)

            total_amount=0
            for product_id, price in rng.sample(products, min(rng.randint(1, 3), len(products))):
                detail_id=f"OD{next_detail:04d}"
                next_detail+=1

                unit_price=price if isinstance(price, (int, float)) and price>0 else round(rng.uniform(199.9, 4199), 2)
                quantity=rng.randint(1, 5)
                total_amount+=unit_price*quantity

                detail={
                    "OrderDetailID":detail_id,
                    "OrderID":order_id,
                    "ProductID":product_id,
                    "Quantity":quantity,
                    "UnitPrice":unit_price,
                }
                details.append(pollute_record(rng, "OrderDetails", detail_id, detail, pollution, error_types, errors_log))

            order={
                "OrderID":order_id,
                "CustomerID":customer_id,
                "OrderDate":get_random_date(rng, start, year_end).isoformat(),
                "TotalAmount":round(total_amount, 2),
            }
            orders.append(pollute_record(rng, "Orders", order_id, order, pollution, error_types, errors_log))

        conn.executemany('''
            INSERT INTO Orders (OrderID, CustomerID, OrderDate, TotalAmount)
            VALUES (:OrderID, :CustomerID, :OrderDate, :TotalAmount)
        ''', orders)
        conn.executemany('''
            INSERT INTO OrderDetails (OrderDetailID, OrderID, ProductID, Quantity, UnitPrice)
            VALUES (:OrderDetailID, :OrderID, :ProductID, :Quantity, :UnitPrice)
        ''', details)
        # Order and its details are polluted separately, so both are rows of this run
        run_id=save_run(conn, "Orders", load_year, pollution, len(orders)+len(details), errors_log)

    return {"run_id":run_id, "inserted":len(orders), "inserted_details":len(details), "polluted":len(errors_log)}


#### STATE OF DB

# Function to get number of rows in every table
def get_tables_counts(db_path):

    with sqlite3.connect(db_path) as conn:
        counts={table:conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in POLLUTABLE_COLUMNS}

    return pd.DataFrame({"Table":list(counts), "Rows":list(counts.values())})


# Function to read log table (empty df if generator was not used, reading does not change db)
def get_log_table(db_path, table, order_col):

    with sqlite3.connect(db_path) as conn:
        table_exists=conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()

        if not table_exists:
            return pd.DataFrame(columns=LOG_COLUMNS[table])

        # reindex, because first version of the table had less columns
        df=pd.read_sql_query(f"SELECT * FROM {table} ORDER BY {order_col} DESC", conn)
        return df.reindex(columns=LOG_COLUMNS[table])


LOG_COLUMNS={
    "Data_Quality_Errors":["ErrorID","RunID","TableName","RecordID","ColumnName","TrueValue","DirtyValue","ErrorType","LoadYear","PollutionLevel","CreatedAt"],
    "Generator_Runs":["RunID","TableName","LoadYear","PollutionLevel","InsertedRows","PollutedRows","CreatedAt"],
}


# Function to get log of inserted errors
def get_errors_log(db_path):
    return get_log_table(db_path, "Data_Quality_Errors", "ErrorID")


# Function to get log of generator runs
def get_runs_log(db_path):
    return get_log_table(db_path, "Generator_Runs", "RunID")


# Function to get errors per year of data delivery (polluted rows / inserted rows)
def get_errors_per_year(df_runs):

    # astype, because empty log from db has object type
    df_runs=df_runs.dropna(subset=["LoadYear"]).astype({"LoadYear":int, "InsertedRows":int, "PollutedRows":int})

    df_years=df_runs.groupby("LoadYear")[["InsertedRows","PollutedRows"]].sum().reset_index()
    df_years["PollutedPercent"]=(df_years["PollutedRows"]/df_years["InsertedRows"]*100).round(2)

    return df_years
