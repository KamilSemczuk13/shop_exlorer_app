# Integration tests: SQL queries on data/db_shop.db (database is only read)

import pytest

from config import BEST_PERFORMANCE, CLEAN_DATA, RAW_DATA, TOTAL_SALES
from src.db import (
    creating_dict_to_sql_query,
    get_all_data_from_tables,
    get_customers_select,
    get_customers_where,
    get_orderdetails_where,
    get_orders_where,
    get_products_where,
)
from src.metrics import get_accuracy_values_raw_vs_clean
from src.queries import (
    get_client_data_sales_across_years,
    get_clients_from_db,
    get_specyfic_client_data,
    get_top_performance_countries,
    get_top_perfromance_categories,
    get_years_filter_from_data,
)

CATEGORIES = {"Audio", "Electronics", "Photo", "Tablets", "Wearables"}
COUNTRIES = {"Poland", "Usa", "Germany", "France", "Spain", "China"}
EMPTY_VALUES = ["", "null", "none"]


@pytest.fixture(scope="module")
def raw_years():
    return get_years_filter_from_data(RAW_DATA)


@pytest.fixture(scope="module")
def clean_years():
    return get_years_filter_from_data(CLEAN_DATA)


@pytest.fixture(scope="module")
def clients():
    return get_clients_from_db()["Name"].tolist()


### Years

def test_raw_years_have_empty_year(raw_years):
    assert None in raw_years


def test_clean_years_have_no_empty_year(clean_years):
    assert None not in clean_years
    assert len(clean_years) > 0


### Top Performance

def test_clean_categories_are_only_correct_names(clean_years):
    df = get_top_perfromance_categories(BEST_PERFORMANCE, clean_years, TOTAL_SALES, CLEAN_DATA)

    assert set(df["Category_Fixed"]) == CATEGORIES


def test_raw_categories_have_other_spellings(raw_years):
    df = get_top_perfromance_categories(BEST_PERFORMANCE, raw_years, TOTAL_SALES, RAW_DATA)

    assert not set(df["Category_Fixed"]) <= CATEGORIES


def test_clean_and_raw_categories_have_same_total_sales(raw_years, clean_years):
    # Cleaning categories only groups names, sum of sales has to be the same
    df_clean = get_top_perfromance_categories(BEST_PERFORMANCE, clean_years, TOTAL_SALES, CLEAN_DATA)
    df_raw = get_top_perfromance_categories(BEST_PERFORMANCE, clean_years, TOTAL_SALES, RAW_DATA)

    assert df_clean["TotalSales"].sum() == pytest.approx(df_raw["TotalSales"].sum())


def test_clean_countries_are_only_correct_names(clean_years):
    df = get_top_performance_countries(BEST_PERFORMANCE, clean_years, CLEAN_DATA)

    assert set(df["Country_mapped"]) <= COUNTRIES
    assert df["Country_mapped"].notna().all()


def test_clean_countries_lose_no_sales(clean_years):
    # Every country spelling has to be mapped, so clean data loses only customers without country
    df_clean = get_top_performance_countries(BEST_PERFORMANCE, clean_years, CLEAN_DATA)
    df_raw = get_top_performance_countries(BEST_PERFORMANCE, clean_years, RAW_DATA)

    df_raw_with_country = df_raw[~df_raw["Country_mapped"].str.strip().str.lower().isin(EMPTY_VALUES)]

    assert df_clean["Total_Sale"].sum() == pytest.approx(df_raw_with_country["Total_Sale"].sum())


def test_raw_countries_show_empty_values(clean_years):
    # Raw data is not cleaned: NULL and "" countries are separate positions
    df_raw = get_top_performance_countries(BEST_PERFORMANCE, clean_years, RAW_DATA)
    df_clean = get_top_performance_countries(BEST_PERFORMANCE, clean_years, CLEAN_DATA)

    assert {"NULL", ""} <= set(df_raw["Country_mapped"])
    assert not {"NULL", ""} & set(df_clean["Country_mapped"])


def test_only_clean_data_is_cleaned_from_nulls():
    dict_select_where = creating_dict_to_sql_query(
        [get_customers_select(["CustomerID", "Country"]), 0, 0, 0],
        [get_customers_where(), get_orders_where(), get_orderdetails_where(), get_products_where()],
    )

    df_raw = get_all_data_from_tables(dict_select_where, RAW_DATA)["customers"]
    df_clean = get_all_data_from_tables(dict_select_where, CLEAN_DATA)["customers"]

    # db_shop.db has 4 customers with NULL country and 2 with ""
    assert len(df_raw) == 59
    assert len(df_clean) == 59 - 6


### Deep Dive: Client

def test_raw_client_sales_have_only_this_client(raw_years, clients):
    # Empty year filter (OR OrderYear is Null) can not take rows of other clients
    for client in clients:
        df = get_client_data_sales_across_years(raw_years, client, RAW_DATA)

        assert set(df["Customer"]) <= {client}, client


def test_clean_client_sales_have_no_empty_year(clean_years, clients):
    for client in clients:
        df = get_client_data_sales_across_years(clean_years, client, CLEAN_DATA)

        assert df["OrderYear"].notna().all(), client


def test_accuracy_works_for_every_client(raw_years, clean_years, clients):
    # Client without orders gives empty df (object type), accuracy can not crash
    for client in clients:
        df_raw = get_client_data_sales_across_years(raw_years, client, RAW_DATA)
        df_clean = get_client_data_sales_across_years(clean_years, client, CLEAN_DATA)

        matches, total, _ = get_accuracy_values_raw_vs_clean(df_clean, df_raw, ["OrderYear"], "TotalSales")

        assert 0 <= matches <= total, client


def test_client_monthly_data_has_month_names(clean_years, clients):
    df = get_specyfic_client_data(clean_years, clients[0], CLEAN_DATA)

    assert "Unknown" not in set(df["Month_normal"])
