# Tests of accuracy metrics: comparison of raw data with clean data

import pandas as pd
import pytest

from src.metrics import (
    get_accuracy_raw_vs_clean,
    get_accuracy_values_raw_vs_clean,
    get_category_set_key,
    get_category_sets_raw_vs_clean,
)


def leaderboard(names):
    # Leaderboard df with rank 1..n in the given order
    return pd.DataFrame({"Name": names, "Rank": range(1, len(names) + 1)})


### get_accuracy_raw_vs_clean (position by position)

def test_accuracy_all_positions_match():
    df = leaderboard(["Camera", "Earphones", "Tablet"])

    matches, total, _ = get_accuracy_raw_vs_clean(df, df, "Name", "Name", "Rank")

    assert (matches, total) == (3, 3)


def test_accuracy_counts_only_same_positions():
    df_clean = leaderboard(["Camera", "Earphones", "Tablet"])
    df_raw = leaderboard(["camera", "Earphones", "Tablet X"])

    matches, total, df_comparison = get_accuracy_raw_vs_clean(df_clean, df_raw, "Name", "Name", "Rank")

    assert (matches, total) == (1, 3)
    assert df_comparison["Match"].tolist() == ["❌", "✅", "❌"]


def test_accuracy_same_names_in_other_order_do_not_match():
    df_clean = leaderboard(["Camera", "Earphones"])
    df_raw = leaderboard(["Earphones", "Camera"])

    matches, total, _ = get_accuracy_raw_vs_clean(df_clean, df_raw, "Name", "Name", "Rank")

    assert (matches, total) == (0, 2)


def test_accuracy_sorts_by_rank_not_by_row_order():
    df_clean = leaderboard(["Camera", "Earphones"])
    df_raw = pd.DataFrame({"Name": ["Earphones", "Camera"], "Rank": [2, 1]})

    matches, total, _ = get_accuracy_raw_vs_clean(df_clean, df_raw, "Name", "Name", "Rank")

    assert (matches, total) == (2, 2)


def test_accuracy_longer_list_is_the_base():
    df_clean = leaderboard(["Audio", "Photo"])
    df_raw = leaderboard(["Audio", "Photo", "audio", "photo"])

    matches, total, df_comparison = get_accuracy_raw_vs_clean(df_clean, df_raw, "Name", "Name", "Rank")

    assert (matches, total) == (2, 4)
    assert df_comparison["Clean"].tolist()[2:] == [None, None]


def test_accuracy_different_column_names():
    # Months: clean is compared by number, raw has numbers in renamed column
    df_clean = pd.DataFrame({"Month": [3.0, 9.0], "Rank": [1, 2]})
    df_raw = pd.DataFrame({"Month_Maped": [3.0, 9.0], "Rank": [1, 2]})

    matches, total, _ = get_accuracy_raw_vs_clean(df_clean, df_raw, "Month", "Month_Maped", "Rank")

    assert (matches, total) == (2, 2)


def test_accuracy_empty_data():
    df = leaderboard([])

    matches, total, df_comparison = get_accuracy_raw_vs_clean(df, df, "Name", "Name", "Rank")

    assert (matches, total) == (0, 0)
    assert df_comparison.empty


def test_accuracy_comparison_index_starts_from_1():
    df = leaderboard(["Camera", "Earphones"])

    _, _, df_comparison = get_accuracy_raw_vs_clean(df, df, "Name", "Name", "Rank")

    assert df_comparison.index.tolist() == [1, 2]


### get_accuracy_values_raw_vs_clean (values for the same keys)

def test_values_match_after_rounding():
    df_clean = pd.DataFrame({"Year": [2023.0, 2024.0], "Sales": [100.004, 200.0]})
    df_raw = pd.DataFrame({"Year": [2023.0, 2024.0], "Sales": [100.0, 200.0]})

    matches, total, _ = get_accuracy_values_raw_vs_clean(df_clean, df_raw, ["Year"], "Sales")

    assert (matches, total) == (2, 2)


def test_values_different_value_is_mismatch():
    df_clean = pd.DataFrame({"Year": [2023.0], "Sales": [1498.6]})
    df_raw = pd.DataFrame({"Year": [2023.0], "Sales": [1098.8]})

    matches, total, _ = get_accuracy_values_raw_vs_clean(df_clean, df_raw, ["Year"], "Sales")

    assert (matches, total) == (0, 1)


def test_values_key_only_in_one_version_is_mismatch():
    # Raw has sales with empty year, clean does not
    df_clean = pd.DataFrame({"Year": [2023.0, 2024.0], "Sales": [16992.4, 14795.98]})
    df_raw = pd.DataFrame({"Year": [None, 2023.0, 2024.0], "Sales": [10996.0, 16992.4, 14795.98]})

    matches, total, df_comparison = get_accuracy_values_raw_vs_clean(df_clean, df_raw, ["Year"], "Sales")

    assert (matches, total) == (2, 3)
    assert df_comparison["Match"].tolist().count("❌") == 1


def test_values_with_many_keys():
    df_clean = pd.DataFrame({
        "Category_mapped": ["Electronics", "Electronics"],
        "Month": [8.0, 11.0],
        "Sales": [3899.0, 3999.0],
    })
    df_raw = pd.DataFrame({
        "Category_mapped": ["Electronics", "electronics"],
        "Month": [8.0, 11.0],
        "Sales": [3899.0, 3999.0],
    })

    matches, total, df_comparison = get_accuracy_values_raw_vs_clean(df_clean, df_raw, ["Category_mapped", "Month"], "Sales")

    assert (matches, total) == (1, 3)
    assert list(df_comparison.columns) == ["Category_mapped", "Month", "Clean", "Raw", "Match"]


def test_values_empty_data():
    df = pd.DataFrame(columns=["Year", "Sales"])

    matches, total, _ = get_accuracy_values_raw_vs_clean(df, df, ["Year"], "Sales")

    assert (matches, total) == (0, 0)


### Category sets

@pytest.mark.parametrize("category", ["Electronics", "electronics", "ELECTRONICS", " Electro nics "])
def test_category_set_key_is_normalized(category):
    assert get_category_set_key(category) == "electronics"


def test_category_sets_group_raw_variants_with_clean_name():
    df_clean = pd.DataFrame({"Category_mapped": ["Electronics", "Tablets"], "Sales": [1, 2]})
    df_raw = pd.DataFrame({"Category_mapped": ["Electronics", "electronics", "TABLETS"], "Sales": [1, 1, 2]})

    dict_sets = get_category_sets_raw_vs_clean(df_clean, df_raw)

    assert list(dict_sets) == ["electronics", "tablets"]

    set_name, df_set_clean, df_set_raw = dict_sets["electronics"]
    assert set_name == "Electronics"
    assert len(df_set_clean) == 1
    assert df_set_raw["Category_mapped"].tolist() == ["Electronics", "electronics"]

    # Name of the set is taken from clean data even when raw has other spelling
    assert dict_sets["tablets"][0] == "Tablets"


def test_category_set_only_in_raw_takes_raw_name():
    df_clean = pd.DataFrame({"Category_mapped": ["Audio"], "Sales": [1]})
    df_raw = pd.DataFrame({"Category_mapped": ["Audio", "photo"], "Sales": [1, 2]})

    dict_sets = get_category_sets_raw_vs_clean(df_clean, df_raw)

    set_name, df_set_clean, df_set_raw = dict_sets["photo"]
    assert set_name == "photo"
    assert df_set_clean.empty
    assert len(df_set_raw) == 1
