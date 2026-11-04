# Tests of transforming data with pandas: mapping, cleaning, merging tables

import pandas as pd
import pytest

from config import BEST_PERFORMANCE, CLEAN_DATA, RAW_DATA, WORST_PERFORMANCE
from src.transform import (
    cleaning_data,
    get_cleaned_data,
    get_concated_categories_df,
    get_map_month,
    get_mapped_categories_df,
    get_mapped_countries_df,
    get_merged_top_performance_country,
    get_monthly_chart_values,
    get_performance_python,
    get_valid_values_df,
)


### Mapping

@pytest.mark.parametrize("month, expected", [(1, "January"), (2, "February"), (3.0, "March"), (12, "December")])
def test_map_month(month, expected):
    assert get_map_month(month) == expected


@pytest.mark.parametrize("month", [0, 13, None, "x"])
def test_map_month_unknown(month):
    assert get_map_month(month) == "Unknown"


# Every spelling of the country that exists in db_shop.db
@pytest.mark.parametrize("country, expected", [
    ("Poland", "Poland"), ("POLAND", "Poland"), ("Polska", "Poland"), ("polska", "Poland"),
    ("POLSKA", "Poland"), ("Polonia", "Poland"), ("PL", "Poland"), ("pL", "Poland"),
    ("USA", "Usa"), ("United States", "Usa"),
    ("Germany", "Germany"), ("germany", "Germany"),
    ("France", "France"), ("España", "Spain"),
    ("China", "China"), ("Chiny", "China"),
    (" poland ", "Poland"),
])
def test_mapped_countries_clean(country, expected):
    df = pd.DataFrame({"Country": [country]})

    df = get_mapped_countries_df(df, CLEAN_DATA)

    assert df["Country_mapped"].iloc[0] == expected


def test_mapped_countries_raw_keeps_original_values():
    df = pd.DataFrame({"Country": ["POLAND", "pL"]})

    df = get_mapped_countries_df(df, RAW_DATA)

    assert df["Country_mapped"].tolist() == ["POLAND", "pL"]


# Every spelling of the category that exists in db_shop.db
@pytest.mark.parametrize("category, expected", [
    ("Audio", "Audio"), ("audio", "Audio"),
    ("Electronics", "Electronics"), ("electronics", "Electronics"),
    ("Photo", "Photo"), ("photo", "Photo"),
    ("Tablets", "Tablets"), ("TABLETS", "Tablets"),
    ("Wearables", "Wearables"),
])
def test_mapped_categories(category, expected):
    df = pd.DataFrame({"Category": [category]})

    df = get_mapped_categories_df(df)

    assert df["Category_mapped"].iloc[0] == expected


@pytest.mark.parametrize("performance, expected", [(BEST_PERFORMANCE, False), (WORST_PERFORMANCE, True)])
def test_performance_python(performance, expected):
    assert get_performance_python(performance) == expected


### Cleaning

def test_cleaning_data_removes_nulls_and_fake_nulls():
    df = pd.DataFrame({"Country": ["Poland", None, "", "  ", "null", " NULL ", "None", "France"]})

    df = cleaning_data(df, "Country")

    assert df["Country"].tolist() == ["Poland", "France"]


def test_valid_values_removes_quantity_and_price_out_of_range():
    df = pd.DataFrame({
        "OrderDetailID": ["OD1", "OD2", "OD3", "OD4", "OD5", "OD6"],
        "Quantity": [2, 0, -3, 1, 1, 1],
        "UnitPrice": [100.0, 100.0, 100.0, -299.9, None, 50.0],
    })

    df = get_valid_values_df(df)

    assert df["OrderDetailID"].tolist() == ["OD1", "OD6"]


def test_merged_top_performance_country_clean_skips_values_out_of_range():
    tables = tables_for_countries()
    tables["orderdetails"]["Quantity"] = [1, -2, 1]

    df_clean = get_merged_top_performance_country(tables, BEST_PERFORMANCE, CLEAN_DATA)
    df_raw = get_merged_top_performance_country(tables_for_countries() | {"orderdetails": tables["orderdetails"]}, BEST_PERFORMANCE, RAW_DATA)

    # Clean: only valid order detail of Poland (100), raw: 100 + (-100)
    assert df_clean.set_index("Country_mapped")["Total_Sale"].to_dict() == {"France": 150.0, "Poland": 100.0}
    assert df_raw.set_index("Country_mapped")["Total_Sale"].to_dict() == {"France": 150.0, "PL": -100.0, "Polska": 100.0}


def test_cleaned_data_checks_every_column():
    df = pd.DataFrame({
        "CustomerID": [1, 2, 3],
        "Country": ["Poland", "France", None],
        "OrderDate": ["2023-01-01", "null", "2023-02-01"],
    })

    df = get_cleaned_data(df)

    assert df["CustomerID"].tolist() == [1]


### Merging

def tables_for_countries():
    return {
        "customers": pd.DataFrame({"CustomerID": [1, 2, 3], "Country": ["Polska", "PL", "France"]}),
        "orders": pd.DataFrame({"CustomerID": [1, 2, 3], "OrderID": [10, 20, 30]}),
        "orderdetails": pd.DataFrame({"OrderID": [10, 20, 30], "Quantity": [1, 2, 1], "UnitPrice": [100.0, 50.0, 150.0]}),
    }


def test_merged_top_performance_country_clean_groups_spellings():
    df = get_merged_top_performance_country(tables_for_countries(), BEST_PERFORMANCE, CLEAN_DATA)

    assert df["Country_mapped"].tolist() == ["Poland", "France"]
    assert df["Total_Sale"].tolist() == [200.0, 150.0]
    assert df["RankedSales"].tolist() == [1.0, 2.0]


def test_merged_top_performance_country_raw_keeps_spellings():
    df = get_merged_top_performance_country(tables_for_countries(), BEST_PERFORMANCE, RAW_DATA)

    assert sorted(df["Country_mapped"]) == ["France", "PL", "Polska"]


def test_merged_top_performance_country_worst():
    df = get_merged_top_performance_country(tables_for_countries(), WORST_PERFORMANCE, CLEAN_DATA)

    assert df["Country_mapped"].tolist() == ["France", "Poland"]


### Helpers for charts and accuracy

def test_monthly_chart_values_is_mean_per_year_and_month():
    df = pd.DataFrame({
        "OrderYear": [2023.0, 2023.0, 2024.0],
        "Month": [6.0, 6.0, 6.0],
        "TotalSales": [100.0, 300.0, 50.0],
        "AvgSales": [100.0, 150.0, 50.0],
    })

    df = get_monthly_chart_values(df)

    assert df["TotalSales"].tolist() == [200.0, 50.0]
    assert df["AvgSales"].tolist() == [125.0, 50.0]


def test_monthly_chart_values_keeps_empty_year():
    df = pd.DataFrame({"OrderYear": [None, 2023.0], "Month": [6.0, 6.0], "TotalSales": [1.0, 2.0], "AvgSales": [1.0, 2.0]})

    df = get_monthly_chart_values(df)

    assert len(df) == 2


def test_concated_categories_df():
    dict_df = {
        "Audio": pd.DataFrame({"Category_mapped": ["Audio"], "Total_Sale_Category": [1.0]}),
        "Photo": pd.DataFrame({"Category_mapped": ["Photo"], "Total_Sale_Category": [2.0]}),
    }

    df = get_concated_categories_df(dict_df)

    assert df["Category_mapped"].tolist() == ["Audio", "Photo"]


def test_concated_categories_df_empty_has_columns():
    df = get_concated_categories_df({})

    assert df.empty
    assert list(df.columns) == ["Category_mapped", "Year", "Month", "Total_Sale_Category"]
