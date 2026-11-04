# Accuracy metrics: comparison of raw data with clean data

import pandas as pd


# Function to compare 1:1 (position by position) clean and raw leaderboard
def get_accuracy_raw_vs_clean(df_clean, df_raw, clean_col, raw_col, rank_col):

    # Same order as in leaderboard
    clean_values=df_clean.sort_values(rank_col, kind="stable")[clean_col].tolist()
    raw_values=df_raw.sort_values(rank_col, kind="stable")[raw_col].tolist()

    # Longer list is the base, missing positions count as mismatch
    total=max(len(clean_values), len(raw_values))
    clean_values+=[None]*(total-len(clean_values))
    raw_values+=[None]*(total-len(raw_values))

    matches=[clean==raw and clean is not None for clean, raw in zip(clean_values, raw_values)]

    df_comparison=pd.DataFrame({
        "Clean":clean_values,
        "Raw":raw_values,
        "Match":["✅" if match else "❌" for match in matches]
    })
    df_comparison.index=df_comparison.index+1

    return sum(matches), total, df_comparison


# Function to compare 1:1 values of clean and raw data for the same keys (e.g. year, month)
def get_accuracy_values_raw_vs_clean(df_clean, df_raw, key_cols, value_col):

    df_comparison=df_clean[key_cols+[value_col]].merge(
        df_raw[key_cols+[value_col]],
        how="outer",
        on=key_cols,
        suffixes=("_clean","_raw")
    )
    df_comparison=df_comparison.rename(columns={f"{value_col}_clean":"Clean", f"{value_col}_raw":"Raw"})

    # Key missing in one of the versions counts as mismatch (NaN != NaN)
    # to_numeric, because empty df from db has object type
    matches=pd.to_numeric(df_comparison["Clean"]).round(2)==pd.to_numeric(df_comparison["Raw"]).round(2)
    df_comparison["Match"]=["✅" if match else "❌" for match in matches]
    df_comparison.index=df_comparison.index+1

    return int(matches.sum()), len(df_comparison), df_comparison


# Function to get name of the set, so "electronics" and "Electronics" are in the same set
def get_category_set_key(category):

    return str(category).replace(" ","").lower()


# Function to split clean and raw df into sets per category
def get_category_sets_raw_vs_clean(df_clean, df_raw):

    df_clean=df_clean.assign(Set=df_clean["Category_mapped"].apply(get_category_set_key))
    df_raw=df_raw.assign(Set=df_raw["Category_mapped"].apply(get_category_set_key))

    # Key: set key (e.g. "electronics"), value: (set name, clean df, raw df)
    dict_sets={}
    for set_key in sorted(set(df_clean["Set"]) | set(df_raw["Set"])):

        df_set_clean=df_clean[df_clean["Set"]==set_key]
        df_set_raw=df_raw[df_raw["Set"]==set_key]

        # Name of the set from clean data if exists
        if len(df_set_clean)>0:
            set_name=df_set_clean["Category_mapped"].iloc[0]
        else:
            set_name=df_set_raw["Category_mapped"].iloc[0]

        dict_sets[set_key]=(set_name, df_set_clean, df_set_raw)

    return dict_sets
