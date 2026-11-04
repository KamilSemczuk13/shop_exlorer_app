# Transforming data with pandas: mapping, cleaning, merging tables

import pandas as pd
import streamlit as st

from config import BEST_PERFORMANCE, RAW_DATA, WORST_PERFORMANCE


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
    else:
        # Removing every space, so "United States" is "unitedstates"
        df["Country_mapped"]=df["Country"].astype(str).str.replace(" ","").str.lower().map(COUNTRIES_DICT)

    

    return df


def get_mapped_categories_df(df):

    df["Category_mapped"]=df["Category"].astype(str).str.strip().str.lower().map(CATEGORIES_DICT)

    return df


# Function to cleaning data from nulls and fake nulls
def cleaning_data(df, col):

    return df[
        (df[col].notna()) & (df[col].astype(str).str.strip() != "") &
        (df[col].astype(str).str.strip().str.lower() != "null") & 
        (df[col].astype(str).str.strip().str.lower() != "none")
    ]


# Function to remove order details with values out of range (Quantity <= 0, price <= 0)
def get_valid_values_df(df):

    quantity=pd.to_numeric(df["Quantity"], errors="coerce")
    unit_price=pd.to_numeric(df["UnitPrice"], errors="coerce")

    return df[(quantity>0) & (unit_price>0)]


# Geting cleaned df
def get_cleaned_data(df):

    for col in df.columns:
        df=cleaning_data(df, col)

    return df


# get Top performance countries
def get_merged_top_performance_country(dict_of_tables, performance, data_version):

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
    df_grouped_country_sales=(df_final_merged_ranked.groupby("Country_mapped").sum()
                          ).reset_index()
    df_grouped_country_sales=df_grouped_country_sales.sort_values("Total_Sale", ascending=performance)
    df_grouped_country_sales["RankedSales"]=df_grouped_country_sales["Total_Sale"].rank(ascending=performance)

    return df_grouped_country_sales


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
    else:
        try:
            df_o_cl=get_mapped_month_df(df_o_cl)
        except Exception as ex:
            st.error(f"No key of month found, error: {ex}")
                     
        try:
            df_p_cl=get_mapped_categories_df(df_p_cl)
        except Exception as ex:
            st.error(f"No key of category found, error: {ex}")

        # Clean data has no values out of range
        df_od_cl=get_valid_values_df(df_od_cl)

    df_c_o=df_o_cl.merge(df_c_cl, how="inner",on="CustomerID")
    df_c_o_od=df_c_o.merge(df_od_cl, how="inner", on="OrderID")
    df_c_o_od_p=df_c_o_od.merge(df_p_cl, how="inner", on="ProductID")
    df_c_o_od_p["Total_Sale"]=df_c_o_od_p["Quantity"]*df_c_o_od_p["UnitPrice"]

    # get df with avreage and sum of monthly Total sales of categories
    df_grouped_categories_sales=(df_c_o_od_p.groupby(["Category_mapped","Month_mapped","Month","Year"]).agg(

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
