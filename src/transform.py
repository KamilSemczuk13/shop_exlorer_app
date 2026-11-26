# Transforming data with pandas: mapping, cleaning, merging tables

import pandas as pd
import streamlit as st

from config import AVG_SALES, BEST_PERFORMANCE, MAX_SALE, MIN_SALE, RAW_DATA, TOTAL_SALES, WORST_PERFORMANCE


# How NULL is shown in raw data
NULL_LABEL="NULL"


# Every known spelling of the country (lower, without spaces) -> correct name
COUNTRIES_DICT={
    "polska":"Poland", "pl":"Poland", "poland":"Poland", "polonia":"Poland",
    "usa":"Usa", "unitedstates":"Usa",
    "niemcy":"Germany","germany":"Germany", "de":"Germany",
    "france":"France","fr":"France","francja":"France",
    "spain":"Spain", "espana":"Spain", "esp":"Spain", "hiszpania":"Spain","españa":"Spain",
    "china":"China", "chiny":"China"
    }

# Category (lower) -> correct name
CATEGORIES_DICT={
    "electronics":"Electronics",
    "tablets":"Tablets",
    "audio":"Audio",
    "photo":"Photo",
    "wearables":"Wearables"
}

# Metric of sale -> pandas aggregation (the same as sql SUM, AVG, MAX, MIN)
SALE_DICT_TO_GROUP={
    TOTAL_SALES:"sum",
    AVG_SALES:"mean",
    MAX_SALE:"max",
    MIN_SALE:"min"
}


# Function to get choosen performance to python sort
def get_performance_python(performance):
    performance_dict={
        BEST_PERFORMANCE:False,
        WORST_PERFORMANCE:True
    }

    return performance_dict[performance]


# Maping Months
def get_map_month(month):
    month_dict={
        1:"January",
        2:"February",
        3:"March",
        4:"April",
        5:"May",
        6:"June",
        7:"July",
        8:"August",
        9:"September",
        10:"October",
        11:"November",
        12:"December"
    }

    if month in month_dict:
        month=month_dict[month]
    else: 
        month="Unknown"
    return month


# Function to get mapped month
def get_mapped_month_df(df):

    df["Month_mapped"]=df["Month"].apply(get_map_month)

    return df


# Function to get mapped countries column
def get_mapped_countries_df(df, data_version):

    if data_version==RAW_DATA:
        df=df.rename(columns={"Country":"Country_mapped"})
        # groupby skips NaN, so NULL is shown as text in raw data
        df["Country_mapped"]=df["Country_mapped"].fillna(NULL_LABEL)
    else:
        # Removing every space, so "United States" is "unitedstates"
        df["Country_mapped"]=df["Country"].astype(str).str.replace(" ","").str.lower().map(COUNTRIES_DICT)

    

    return df


def get_mapped_categories_df(df):

    df["Category_mapped"]=df["Category"].astype(str).str.strip().str.lower().map(CATEGORIES_DICT)

    return df


# Function to get mask of rows without nulls and fake nulls in column (True = row is kept)
def get_not_null_mask(df, col):

    return (
        (df[col].notna()) & (df[col].astype(str).str.strip() != "") &
        (df[col].astype(str).str.strip().str.lower() != "null") &
        (df[col].astype(str).str.strip().str.lower() != "none")
    )


# Function to cleaning data from nulls and fake nulls
def cleaning_data(df, col):

    return df[get_not_null_mask(df, col)]


# Function to get mask of order details with values in range (True = row is kept)
def get_valid_values_mask(df):

    quantity=pd.to_numeric(df["Quantity"], errors="coerce")
    unit_price=pd.to_numeric(df["UnitPrice"], errors="coerce")

    return (quantity>0) & (unit_price>0)


# Function to remove order details with values out of range (Quantity <= 0, price <= 0)
def get_valid_values_df(df):

    return df[get_valid_values_mask(df)]


# Function to get mask of rows that get_cleaned_data keeps (null in any column removes row)
def get_cleaned_data_mask(df):

    mask=pd.Series(True, index=df.index)
    for col in df.columns:
        mask&=get_not_null_mask(df, col)

    return mask


# Function to count rows that cleaning removes, df is not changed
def get_rejected_rows_count(df, mask_function=get_cleaned_data_mask):

    return int((~mask_function(df)).sum())


# Geting cleaned df
def get_cleaned_data(df):

    for col in df.columns:
        df=cleaning_data(df, col)

    return df


# Geting cleaned df and number of removed rows
def get_cleaned_data_with_count(df):

    df_cleaned=get_cleaned_data(df)

    return df_cleaned, len(df)-len(df_cleaned)


# get Top performance countries
def get_merged_top_performance_country(dict_of_tables, performance, sale, data_version):

    performance=get_performance_python(performance)
    # c-> customers
    # o-> orders
    # od-> orderdetails
    # p -> products

    # Geting data from every tab nedeed
    df_c_cl=dict_of_tables["customers"]
    df_o_cl=dict_of_tables["orders"]
    df_od_cl=dict_of_tables["orderdetails"]
    
    try:
        df_c_cl=get_mapped_countries_df(df_c_cl,data_version)
    except Exception as ex:
        st.error(f"No key of category found, error: {ex}")

    # Clean data has no values out of range
    if data_version!=RAW_DATA:
        df_od_cl=get_valid_values_df(df_od_cl)

    df_c_o=df_o_cl.merge(df_c_cl, how="left",on="CustomerID")
    df_c_o_od=df_c_o.merge(df_od_cl, how="inner", on="OrderID")
    df_c_o_od["Total_Sale"]=df_c_o_od["Quantity"]*df_c_o_od["UnitPrice"]
    df_final_merged_ranked=df_c_o_od[["Country_mapped","Total_Sale" ]]
    df_grouped_country_sales=(df_final_merged_ranked
        .groupby("Country_mapped")["Total_Sale"]
        .agg(SALE_DICT_TO_GROUP[sale])
        .reset_index())
    df_grouped_country_sales=df_grouped_country_sales.sort_values("Total_Sale", ascending=performance)
    # method="min" gives the same ranks as sql rank() in other tabs (ties: 1, 2, 2, 4)
    df_grouped_country_sales["RankedSales"]=df_grouped_country_sales["Total_Sale"].rank(ascending=performance, method="min")

    return df_grouped_country_sales


# Function to get metric of sale per group, NULL group is kept (like sql GROUP BY)
def get_grouped_sales(df, group_col, sale_col, sale):

    grouped=df.groupby(group_col, dropna=False)[sale_col]

    # min_count=1: sum of only NULL sales is NULL (like sql SUM), not 0
    if sale==TOTAL_SALES:
        return grouped.sum(min_count=1)

    return grouped.agg(SALE_DICT_TO_GROUP[sale])


# Function to get top 10 categories from rows of sales (Category, Sale), the same as sql rank()
def get_top_performance_categories_df(df, performance, sale, data_version):

    ascending=get_performance_python(performance)

    if data_version==RAW_DATA:
        df=df.rename(columns={"Category":"Category_mapped"})
    else:
        # Category that can not be mapped (NULL, "null", "") is not in clean data, before ranking
        df=get_mapped_categories_df(df).dropna(subset=["Category_mapped"])


    df_grouped=get_grouped_sales(df, "Category_mapped", "Sale", sale).reset_index(name="TotalSales")

    # Clean data has no NULL sales (sql: Having TotalSales is not null)
    if data_version!=RAW_DATA:
        df_grouped=df_grouped.dropna(subset=["TotalSales"])

    # Sql treats NULL as the lowest value: last in desc, first in asc, method="min" gives ties like sql rank()
    df_grouped["RankedCategorysBySales"]=df_grouped["TotalSales"].rank(
        ascending=ascending, method="min", na_option="top" if ascending else "bottom"
    ).astype(int)

    df_grouped=df_grouped[df_grouped["RankedCategorysBySales"]<=10].sort_values("RankedCategorysBySales", kind="stable")
    # NULL category is shown as None, like in result of sql
    df_grouped["Category_mapped"]=df_grouped["Category_mapped"].astype(object).where(df_grouped["Category_mapped"].notna(), None)

    return df_grouped.reset_index(drop=True)


# Function to get df of merged categories of client sales
def get_merged_categories_sales_of_client(dict_of_tables, data_version):
    # c-> customers
    # o-> orders
    # od-> orderdetails
    # p -> products

    # Geting data from every tab nedeed
    df_c_cl=dict_of_tables["customers"]
    df_o_cl=dict_of_tables["orders"]
    df_od_cl=dict_of_tables["orderdetails"]
    df_p_cl=dict_of_tables["products"]

    if data_version==RAW_DATA:
        df_o_cl["Month_mapped"]=df_o_cl["Month"]
        df_p_cl=df_p_cl.rename(columns={"Category":"Category_mapped"})
        # groupby skips NaN, so NULL is shown as text in raw data
        df_p_cl["Category_mapped"]=df_p_cl["Category_mapped"].fillna(NULL_LABEL)
    else:
                     
        try:
            df_p_cl=get_mapped_categories_df(df_p_cl)
        except Exception as ex:
            st.error(f"No key of category found, error: {ex}")

        # Clean data has no values out of range
        df_od_cl=get_valid_values_df(df_od_cl)
    try:
        df_o_cl=get_mapped_month_df(df_o_cl)
    except Exception as ex:
        st.error(f"No key of month found, error: {ex}")

    # Month of impossible date (only in raw data) is shown as NULL
    df_o_cl.loc[df_o_cl["Month"].isna(), "Month_mapped"]=NULL_LABEL

    df_c_o=df_o_cl.merge(df_c_cl, how="inner",on="CustomerID")
    df_c_o_od=df_c_o.merge(df_od_cl, how="inner", on="OrderID")
    df_c_o_od_p=df_c_o_od.merge(df_p_cl, how="inner", on="ProductID")
    df_c_o_od_p["Total_Sale"]=df_c_o_od_p["Quantity"]*df_c_o_od_p["UnitPrice"]

    # get df with avreage and sum of monthly Total sales of categories
    # Raw data keeps orders with NULL year and month, clean data skips category that can not be mapped (NaN)
    df_grouped_categories_sales=(df_c_o_od_p.groupby(["Category_mapped","Month_mapped","Month","Year"], dropna=data_version!=RAW_DATA).agg(

        Avg_Sale=("Total_Sale","mean"),
        Total_Sale_Category=("Total_Sale","sum")

    )).reset_index()

    return df_grouped_categories_sales


# Fucntion to get dictionary categories 
def get_dict_of_df_categories(df,data_version):

    df=get_merged_categories_sales_of_client(df,data_version)
    dict_df={}
    existing_keys=[]

    for value in df["Category_mapped"]:
        if value in existing_keys:
            continue
        existing_keys.append(value)
        df_get=df[df["Category_mapped"]==value]
        df_get=df_get.sort_values("Month", ascending=True)
        dict_df[value]=df_get

    return dict_df


# Function to get values that monthly chart is showing (barplot shows mean per month and year)
def get_monthly_chart_values(df):

    return df.groupby(["OrderYear","Month"], dropna=False)[["TotalSales","AvgSales"]].mean().reset_index()


# Function to get one df from dictionary of categories
def get_concated_categories_df(dict_df):

    if not dict_df:
        return pd.DataFrame(columns=["Category_mapped","Year","Month","Total_Sale_Category"])

    return pd.concat(dict_df.values(), ignore_index=True)
