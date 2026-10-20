# Tests of building SELECT / WHERE queries

from config import ALL_YEARS
from src.db import (
    build_select,
    build_where,
    get_orders_where,
    get_string_of_years_to_filter,
    get_string_of_years_to_filter_v2,
)


def test_string_of_years():
    assert get_string_of_years_to_filter(["2023", "2024"]) == "(2023,2024)"


def test_string_of_years_one_year():
    assert get_string_of_years_to_filter(["2025"]) == "(2025)"


def test_string_of_years_v2_without_none():
    assert get_string_of_years_to_filter_v2(["2023", "2024"]) == ("(2023,2024)", False)


def test_string_of_years_v2_with_none():
    assert get_string_of_years_to_filter_v2([None, "2023"]) == ("(2023)", True)


def test_build_select():
    assert build_select(["CustomerID", "Country"]) == "CustomerID , Country"


def test_build_select_table_not_used():
    assert build_select(0) == 0


def test_build_where_list_of_years():
    assert build_where(get_orders_where(year=["2023", "2024"])) == "Year in(2023,2024)"


def test_build_where_string_and_int():
    assert build_where({"Customer": "Jan Kowal", "Quantity": 2}) == "Customer='Jan Kowal' AND Quantity=2"


def test_build_where_skips_zero_and_all_years():
    assert build_where({"Customer": "Jan Kowal", "Country": 0, "Year": ALL_YEARS}) == "Customer='Jan Kowal'"


def test_build_where_nothing_to_filter():
    assert build_where({"Customer": 0, "Country": 0}) == 0
