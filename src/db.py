# Connection to SQLite and building SELECT / WHERE queries from tables

import pandas as pd
import sqlite3

from config import ALL_YEARS, DB_PATH
from src.transform import get_cleaned_data


# Db that app is connected to (original or mutable), chosen in sidebar
current_db_path=DB_PATH


# Function to change db that every query is using
def set_db_path(db_path):
    global current_db_path
    current_db_path=db_path


def get_db_path():
    return current_db_path


# Functions to connect and get df from sql data
def get_df_from_db(query):

    with sqlite3.connect(get_db_path()) as conn:

        cursor=conn.execute(query)
        
        data=cursor.fetchall()

    columns=[description[0] for description in cursor.description]

    # Creating df from data extract with query
    df=pd.DataFrame(data, columns=columns)

    return df


def get_string_of_years_to_filter(years):

    conditions=""
    for year in years:
        if year is None:
            conditions+="None"
        else:
            conditions+=f"{year}"
        if year!=years[-1]:
            conditions+=","


    return f'({conditions})'


def get_string_of_years_to_filter_v2(years):

    none_exist = any(year is None for year in years)
    filtered_years = [str(year) for year in years if year is not None]
    conditions = ",".join(filtered_years)

    return f"({conditions})", none_exist


# Geting specyfic data from every tab that is needed
def get_specyfic_data_from_any_tab(select,where,from_var):

    string_select_query=select
    
    string_where_query=where
    if string_where_query==0:
        string_where_query=""
    else:
        string_where_query=f"Where {string_where_query}"

    with sqlite3.connect(get_db_path()) as conn:
        query=f'''
        

        Select
            {string_select_query}
        From {from_var}
        {string_where_query}
        '''

    cursor=conn.execute(query)

    data=cursor.fetchall()

    columns=[description[0] for description in cursor.description]

    df=pd.DataFrame(data, columns=columns)

    return df


# Building string select
def build_select(select_col):
    if select_col==0:
        return 0
    conditions=[]

    # creating select string sql injection
    for col in select_col:
        if col==0:
            continue
        conditions.append(f"{col}")
        
    # returning select string sql injection
    return " , ".join(conditions)


# building string where
def build_where(where_col: dict):
    conditions = []
    for col, val in where_col.items():

        # Checking if value is list for example 2022,2023 year
        if isinstance(val, list):
            string_transformed=f"{col} in"
            string_transformed+=get_string_of_years_to_filter(val)
            return string_transformed
        
        if val in [0, ALL_YEARS]:
            continue  # are not paying attention on 0 values
        if isinstance(val, str):
            conditions.append(f"{col}='{val}'")
        elif isinstance(val, int):
            conditions.append(f"{col}={val}")
        else:
            string_transformed=f"{col} in"
            string_transformed+=get_string_of_years_to_filter(val)
            return conditions.append(string_transformed)
        
    if not conditions:  # if every of the value is 0
        return 0   # retrun 0 if every value is 0

    return " AND ".join(conditions)


# Function to get dict of querries to extract data from db
def creating_dict_to_sql_query(list_column_of_tabs, filters_list_dict):

    # get secelct string for each tab
    customers_select=build_select(list_column_of_tabs[0])
    orders_select=build_select(list_column_of_tabs[1])
    orderdetails_select=build_select(list_column_of_tabs[2])
    products_select=build_select(list_column_of_tabs[3])

    # get where string dor each tab
    customers_where=build_where(filters_list_dict[0])
    orders_where=build_where(filters_list_dict[1])
    orderdetails_where=build_where(filters_list_dict[2])
    products_where=build_where(filters_list_dict[3])

    # Dictionary of selects and where to each tab
    dict_of_cols_tabs={
        
        "customers":{
            "select":customers_select,
            "where":customers_where
        },
        "orders":{
            "select":orders_select,
            "where":orders_where
        },
        "orderdetails":{
            "select":orderdetails_select,
            "where":orderdetails_where
        },
        "products":{
            "select":products_select,
            "where":products_where
        },
    }

    return dict_of_cols_tabs


# Get all tabs that are nedeed to analyse
def get_all_data_from_tables(dict_of_cols_tbas):

    # Taking columns from specyfic tab to create sql select query or 0 if not using
    df_customers_ret=dict_of_cols_tbas["customers"]["select"]
    df_orders_ret=dict_of_cols_tbas["orders"]["select"]
    df_orderdetails_ret=dict_of_cols_tbas["orderdetails"]["select"]
    df_products_ret=dict_of_cols_tbas["products"]["select"]

    customers_where=dict_of_cols_tbas["customers"]["where"]
    orders_where=dict_of_cols_tbas["orders"]["where"]
    orderdetails_where=dict_of_cols_tbas["orderdetails"]["where"]
    products_where=dict_of_cols_tbas["products"]["where"]

    # variables to take name of the columns to from in select query
    cust_from_var="Customers"
    or_from_var="Orders"
    od_from_var="Orderdetails"
    pr_from_var="Products"

    # 0 if we dont need table to extract data from
    if df_customers_ret !=0:

        df_customers=get_specyfic_data_from_any_tab(df_customers_ret,customers_where,cust_from_var)
        df_customers_ret=get_cleaned_data(df_customers)

    if df_orders_ret !=0:

        df_orders=get_specyfic_data_from_any_tab(df_orders_ret,orders_where,or_from_var)
        df_orders_ret=get_cleaned_data(df_orders)

    if df_orderdetails_ret !=0:

        df_orderdetails=get_specyfic_data_from_any_tab(df_orderdetails_ret,orderdetails_where,od_from_var)
        df_orderdetails_ret=get_cleaned_data(df_orderdetails)

    if df_products_ret !=0:

        df_products=get_specyfic_data_from_any_tab(df_products_ret,products_where,pr_from_var)
        df_products_ret=get_cleaned_data(df_products)

    # dict of data from tables to return variables
    tabs_dict={
        "customers":df_customers_ret,
        "orders":df_orders_ret,
        "orderdetails":df_orderdetails_ret,
        "products":df_products_ret
    }
    
    return tabs_dict


# get list of columns from customers table
def get_customers_select(select_list):
    return select_list


# get list of columns from orders table
def get_orders_select(select_list):
    return select_list


# get list of columns from orderdetails table
def get_orderdetails_select(select_list):
    return select_list


# get list of columns from products table
def get_products_select(select_list):
    return select_list


# get dict of columns from customer table
def get_customers_where(customer=0,country=0):

    customers_filter={
        "Customer":customer,
        "Country":country
    }
    return customers_filter


# get dict of columns from orders table
def get_orders_where(year=0,month=0):

    orders_filters={
        "Year":year,
        "Month":month
    }
    return orders_filters


# get dict of columns from orderdetails table
def get_orderdetails_where(quantity=0,unitprice=0):
    orderdetails_filters={
        "Quantity":quantity,
        "UnitPrice":unitprice
    }

    return orderdetails_filters


# get dict of columns from products table
def get_products_where(product=0,category=0):
    products_filters={
        "Product":product,
        "Category":category
    }

    return products_filters
