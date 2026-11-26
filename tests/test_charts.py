# Tests of helpers of charts

import pandas as pd

from src.charts import get_year_labels, get_year_labels_order


def test_year_labels_are_integers_and_null():
    assert get_year_labels(pd.Series([2023.0, None, 2022.0])).tolist() == ["2023", "NULL", "2022"]


def test_year_labels_order_null_first():
    assert get_year_labels_order(["2024", "NULL", "2022", "2024"]) == ["NULL", "2022", "2024"]
