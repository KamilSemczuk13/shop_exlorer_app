import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3
import html as html_std

#### STATIC VARIABLES

DB_PATH="db_shop.db"

CUSTOMER_SEC="Check specyfic client"
PRODUCTS_SEC="Check products "

MODE_TOP="🥇Top Performance"
MODE_CLIENT="🔍 Deep Dive: Client"
PRDUCT_INSIGHTS="📦 Product Insights"

BEST_PERFORMANCE="BEST 📈"
WORST_PERFORMANCE="WORST 📉"

ALL_YEARS="All of the years"


#### SESSION STATES
if "page" not in st.session_state:
    st.session_state["page"]="start"

if "mode" not in st.session_state:
    st.session_state["mode"]="main"

if "performance_top" not in st.session_state:
    st.session_state["performance_top"]=""

if 'year_top' not in st.session_state:
    st.session_state["year_top"]=""

if "client_one"not in st.session_state:
    st.session_state["client_one"]=""

if "clients"not in st.session_state:
    st.session_state["clients"]=""

if 'year_client' not in st.session_state:
    st.session_state["year_client"]=""

if "client_tab" not in st.session_state:
    st.session_state["client_tab"]=""



#### FUNCTIONS

# Functions to connect and get df from sql data
def get_df_from_db(query):
        
    with sqlite3.connect(DB_PATH) as conn:

        cursor=conn.execute(query)
        
        data=cursor.fetchall()

    columns=[description[0] for description in cursor.description]

    # Creating df from data extract with query
    df=pd.DataFrame(data, columns=columns)

    return df

### Functions to extracting data with sql queries

# Function to get available years in data
def get_years_filter_from_data():

    query=f'''

        SELECT 
            strftime('%Y', OrderDate) AS OrderYear
        FROM Orders
        Group by OrderYear
        Having OrderYear is not null;
    '''

    # Conecting to db
    data=get_df_from_db(query)

    available_years=[]
    available_years.append(ALL_YEARS)
    for element in data["OrderYear"]:
        available_years.append(element)
    
    return available_years




# Function to get years filters to sql query
def get_years_filter_to_query_sql(year):
    year_group=""
    year_having=""

    if year is not ALL_YEARS:
        year_group=f", OrderYear"
        year_having=f" AND OrderYear ='{year}'"

    return year_group, year_having

# Function to get choosen performance directly to sql query
def get_performance_sql(performance):
    
    performance_dict={
        BEST_PERFORMANCE:"desc",
        WORST_PERFORMANCE:"asc"
    }

    return performance_dict[performance]

# Function to get choosen performance to python sort
def get_performance_python(performance):
    performance_dict={
        BEST_PERFORMANCE:False,
        WORST_PERFORMANCE:True
    }

    return performance_dict[performance]

    

# Function to get customers performance from data
def get_top_perfromance_customers(performance, year, country):

     # Filtring per performance
    performance=get_performance_sql(performance)

    year_group, year_having=get_years_filter_to_query_sql(year)

    query=f'''
        With RankedClientsTab AS(
            Select 
                strftime('%Y', o.OrderDate) AS OrderYear,
                CONCAT(c.FirstName, " ",c.LastName) AS FullName,
                SUM(od.UnitPrice * od.Quantity) AS TotalSales,
                rank() over(order by SUM(od.UnitPrice * od.Quantity) {performance}) AS RankedClientsBySales
            From customers as c
            Inner join orders as o
                On c.CustomerID=o.CustomerID
            Inner join orderdetails as od
                On od.OrderID=o.OrderID
            Group by FullName {year_group}
            Having TotalSales is not null {year_having}
        )

        Select 
            FullName,
            TotalSales,
            RankedClientsBySales
        From RankedClientsTab
        Where RankedClientsBySales<=10;
    '''
    # Conecting to db
    df_customers_top=get_df_from_db(query)
    return df_customers_top

# Function to get products performance from data
def get_top_perfromance_products(performance, year, country):

    # Filtring per performance
    performance=get_performance_sql(performance)

    year_group, year_having=get_years_filter_to_query_sql(year)

    query=f'''
        With RankedProductsTab AS(
            Select 
                strftime('%Y', o.OrderDate) AS OrderYear,
                p.ProductName,
                SUM(od.UnitPrice * od.Quantity) AS TotalSales,
                rank() over(order by SUM(od.UnitPrice * od.Quantity) {performance}) AS RankedProductsBySales
            From products as p
            Inner join orderdetails as od
                On od.ProductID=p.ProductID
            Inner join orders as o
                On o.OrderID=od.OrderID
            Group by p.ProductName{year_group}
            Having TotalSales is not null {year_having}
        )

        Select 
            ProductName,
            TotalSales,
            RankedProductsBySales
        From RankedProductsTab
        Where RankedProductsBySales<=10;
    '''

    
    # Converting data to df
    df_products_top=get_df_from_db(query)
    return df_products_top

# Function to get categories performance from data
def get_top_perfromance_categories(performance, year, country):

     # Filtring per performance
    performance=get_performance_sql(performance)

    year_group, year_having=get_years_filter_to_query_sql(year)
    country=""

    query=f'''
        With RankedCategoryTab AS(
            Select 
                strftime('%Y', o.OrderDate) AS OrderYear,
                Case 
                    When replace(lower(p.Category), " ", "") = "electronics" Then "Electronics"
                    When replace(lower(p.Category)," ","")="audio" Then "Audio"
                    When replace(lower(p.Category), " ","")="photo" Then "Photo"
                    When replace(lower(p.Category), " ","")="tablets" Then "Tablets"
                    When replace(lower(p.Category), " ","")="wearables" Then "Wearables"
                    ELSE p.Category
                END AS Category_Fixed,
                SUM(od.UnitPrice * od.Quantity) AS TotalSales,
                rank() over(order by SUM(od.UnitPrice * od.Quantity) {performance}) AS RankedCategorysBySales
            From products as p
            Inner join orderdetails as od
                On od.ProductID=p.ProductID
            Inner join orders as o
                On o.OrderID=od.OrderID
            Group by Category_Fixed {year_group}
            Having TotalSales is not null {year_having}
        )

        Select 
            Category_Fixed,
            TotalSales,
            RankedCategorysBySales
        From RankedCategoryTab
        Where RankedCategorysBySales<=10;   
    '''

    df_categories_top=get_df_from_db(query)
    return df_categories_top


def get_top_perfromance_moths(performance, year, country):

     # Filtring per performance
    performance=get_performance_sql(performance)

    year_group, year_having=get_years_filter_to_query_sql(year)
    country=""

    query=f'''
        With RankedMonthTab AS(
            Select 
                strftime('%Y', o.OrderDate) AS OrderYear,
                round(strftime('%m',OrderDate),0) AS Month,
                SUM(od.UnitPrice * od.Quantity) AS TotalSales,
                rank() over(order by SUM(od.UnitPrice * od.Quantity) {performance}) AS RankedMonthsBySales
            From products as p
            Inner join orderdetails as od
                On od.ProductID=p.ProductID
            Inner join orders as o
                On o.OrderID=od.OrderID
            Group by Month {year_group}
            Having TotalSales is not null {year_having}
        )

        Select 
            Month,
            TotalSales,
            RankedMonthsBySales
        From RankedMonthTab
        Where RankedMonthsBySales<=10;
    '''

    # Conecting to db
    df_months_top=get_df_from_db(query)
    df_months_top["Month_Maped"]=df_months_top["Month"].apply(get_map_month)
    
    return df_months_top


# Description of action of the leaderboard
def get_description_text_top_mode(performance, tab, type_of_sales, years):
    
    text=f"The LEADERBOARD below is showing you {performance}  *{tab}* in **{type_of_sales}** in **{years}**"

    return text

# Get Clients from db
def get_clients_from_db():
    query='''
    Select 
        Concat(FirstName," ",LastName) AS Name
    From Customers
    Group by Name
    Order by Name;
    ''' 

    clients_df=get_df_from_db(query)
    return clients_df

def get_specyfic_client_data(year, customer):

    year_group, year_having=get_years_filter_to_query_sql(year)
    country=""

    query=f'''

        Select
            o.OrderID as OrderID,
            strftime('%Y', o.OrderDate) AS OrderYear,
            round(strftime('%m',OrderDate),0) AS Month,
            SUM(od.UnitPrice * od.Quantity) AS TotalSales,
            AVG(od.UnitPrice * od.Quantity) AS AvgSales
        From customers as c
        Inner join orders as o
            On c.CustomerID=o.CustomerID
        inner join orderdetails as od
            On O.OrderID=od.OrderID
        Group by o.OrderID,OrderYear, Month
        Having Concat(c.FirstName, " ", c.LastName)="{customer}" {year_having}
    '''

    # Conecting to db
    df_customer_spec=get_df_from_db(query)

    # Cleaning data
    df_customer_spec = df_customer_spec.dropna(subset=["Month"])
    df_customer_spec["Month_normal"]=df_customer_spec["Month"].apply(get_map_month)
    df_customer_spec=df_customer_spec.sort_values("Month", ascending=True)

    return df_customer_spec

def get_categories_of_the_client(year, customer):
    
    year_group, year_having=get_years_filter_to_query_sql(year)
    country=""

    query=f'''

        Select
            Case 
                When replace(lower(p.Category), " ", "") = "electronics" Then "Electronics"
                When replace(lower(p.Category)," ","")="audio" Then "Audio"
                When replace(lower(p.Category), " ","")="photo" Then "Photo"
                When replace(lower(p.Category), " ","")="tablets" Then "Tablets"
                When replace(lower(p.Category), " ","")="wearables" Then "Wearables"
                ELSE p.Category
            END AS Category_Fixed
        From customers as c
        Inner join orders as o
            On c.CustomerID=o.CustomerID
        inner join orderdetails as od
            On O.OrderID=od.OrderID
        inner join products as p
            On p.ProductID=od.ProductID
        Where Concat(c.FirstName, " ", c.LastName)="{customer}";
    '''

    # Conecting to db
    df_category_of_cleint=get_df_from_db(query)
    return df_category_of_cleint


# Geting specyfic data from every tab that is needed
def get_specyfic_data_from_any_tab(select,where,from_var):

    string_select_query=select
    
    string_where_query=where
    if string_where_query==0:
        string_where_query=""
    else:
        string_where_query=f"Where {string_where_query}"

    with sqlite3.connect("db_shop.db") as conn:
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

### Function to transform data with python

# Maping Months
def get_map_month(month):
    month_dict={
        1:"January",
        2:"Feburary",
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
def get_mapped_countries_df(df):

    countries_dict={
        "polska":"Poland", "pl":"Poland", "poland":"Poland", "polonia":"Poland",
        "usa":"Usa", "unitedstates":"Usa",
        "niemcy":"Germany","germany":"Germany", "de":"Germany",
        "france":"France","fr":"France","francja":"France",
        "spain":"Spain", "espana":"Spain", "esp":"Spain", "hiszpania":"Spain","españa":"Spain",
        "china":"China", "Chiny":"China"
        }

    df["Country_mapped"]=df["Country"].astype(str).str.strip().str.lower().map(countries_dict)

    return df

def get_mapped_categories_df(df):
    dict_categories={
        "electronics":"Electronics",
        "tables":"Tables",
        "audio":"Audio",
        "photo":"Photo",
        "wearables":"Wearables"
    }

    df["Category_mapped"]=df["Category"].astype(str).str.strip().str.lower().map(dict_categories)

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
        if val in [0, ALL_YEARS]:
            continue  # are not paying attention on 0 values
        if isinstance(val, str):
            conditions.append(f"{col}='{val}'")
        else:
            conditions.append(f"{col}={val}")

    if not conditions:  # if every of the value is 0
        return 0   # retrun 0 if every value is 0

    return " AND ".join(conditions)

# Function to cleaning data from nulls and fake nulls
def cleaning_data(df, col):

    return df[
        (df[col].notna()) & (df[col].astype(str).str.strip() != "") &
        (df[col].astype(str).str.strip().str.lower() != "null") & 
        (df[col].astype(str).str.strip().str.lower() != "none")
    ]

# Geting cleaned df
def get_cleaned_data(df):

    for col in df.columns:
        df=cleaning_data(df, col)

    return df

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


# get Top performance countries
def get_merged_top_performance_country(dict_of_tables, performance):

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
        df_c_cl=get_mapped_countries_df(df_c_cl)
    except Exception as ex:
        st.error(f"No key of country found, error: {ex}")
        
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
def get_merged_categories_sales_of_client(dict_of_tables):
    # c-> customers
    # o-> orders
    # od-> orderdetails
    # p -> products

    # Geting data from every tab nedeed
    df_c_cl=dict_of_tables["customers"]
    df_o_cl=dict_of_tables["orders"]
    df_od_cl=dict_of_tables["orderdetails"]
    df_p_cl=dict_of_tables["products"]

    try:
        df_o_cl=get_mapped_month_df(df_o_cl)
    except Exception as ex:
        st.error(f"No key of month found, error: {ex}")
                 
    try:
        df_p_cl=get_mapped_categories_df(df_p_cl)
    except Exception as ex:
        st.error(f"No key of category found, error: {ex}")

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
def get_dict_of_df_categories(df):

    df=get_merged_categories_sales_of_client(df)
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

### FUNCTIONS to visualise data

# Visualise leaderboard
def leaderboard_html_inline(df, name_col, score_col, rank_col, performance):
    df = df.sort_values(rank_col, ascending=True).reset_index(drop=True)
    items = []
    for _, row in df.iterrows():
        rank = int(row[rank_col])
        name = row[name_col]
        score = row[score_col]

        if performance==BEST_PERFORMANCE:
            if rank == 1:
                badge, bg = "🥇", "linear-gradient(180deg, #ffd966, #f4c430)"
            elif rank == 2:
                badge, bg = "🥈", "linear-gradient(180deg, #e6e6e6, #cfcfcf)"
            elif rank == 3:
                badge, bg = "🥉", "linear-gradient(180deg, #e7d7c1, #d7b89a)"
            else:
                badge, bg = str(rank), "rgba(220,220,220,0.35)"
        else:
            if rank == 1:
                badge, bg = "🚫", "linear-gradient(180deg, #ff4d4d, #b30000)"
            elif rank == 2:
                badge, bg = "📉", "linear-gradient(180deg, #ffa500, #cc7000)"
            elif rank == 3:
                badge, bg = "🔥", "linear-gradient(180deg, #f5d76e, #c9a300)"
            else:
                badge, bg = str(rank), "rgba(220,220,220,0.35)"

        items.append(f"""
        <div style="
            display:flex; align-items:center; justify-content:space-between;
            padding:12px 16px; margin-bottom:10px; border-radius:10px;
            background:{bg}; box-shadow:0 1px 3px rgba(0,0,0,0.1);
            font-family:Segoe UI, Roboto, Arial, sans-serif;">
            <div style="font-weight:700; font-size:20px; min-width:50px; text-align:center;">{badge}</div>
            <div style="flex:1; display:flex; justify-content:space-between; align-items:center; margin-left:12px;">
                <div style="font-weight:600; font-size:16px;">{name}</div>
                <div style="font-weight:700; font-size:18px;">{score:,.0f}$</div>
            </div>
        </div>
        """)
        
    return "\n".join(items)

# Get monthly total sales chart
def get_monthly_sales_chart(df, type_of_sales, customer,year):

    sales_desc={
        "TotalSales":"Total Sales",
        "AvgSales": "Average Sales"
    }

    sns.set_style("whitegrid")  
    sns.set_palette("tab10")    

    # creating plot
    fig, ax = plt.subplots(figsize=(10,5))
    sns.lineplot(
        x="Month_normal",
        y=f"{type_of_sales}",
        hue="OrderYear",
        data=df,
        marker="o",   
        ax=ax
    )

    # Tittle and series osi
    ax.set_title(f"Monthly {sales_desc[type_of_sales]} of {customer} in {year}", fontsize=16)
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel(f"{sales_desc[type_of_sales]}", fontsize=12)

    # adding legend
    ax.legend(title="Year", title_fontsize=12, fontsize=10, loc='upper left')

    return fig

# Function to Display average and total sales of customer 
def display_charts_monthly_sales_per_customer(df, customer, year):

    st.info(f"The chart showing monthly Sales of {customer} in {year}🔻 ")
    # Seaborn style
    
    # Get total sales chart
    fig=get_monthly_sales_chart(df, "TotalSales",customer, year)

    # Displaying in Streamlit 
    st.pyplot(fig)
    st.markdown("")

    st.info(f"The chart showing monthly Average Sales of {customer} in {year}🔻")

    # Get average sales 
    fig=get_monthly_sales_chart(df,"AvgSales",customer,year)

    # Displaying in Streamlit 
    st.pyplot(fig)

def get_barplot_of_category_client_monthly_sales(df,customer,category,year):

    fig, ax=plt.subplots(figsize=(6,3))

    sns.barplot(
        data=df,
        x="Month_mapped",
        y="Total_Sale_Category",
        hue="Year"
    )

    ax.set_title(f"{customer}`s monthly {category} sales in {year}")

    ax.set_ylabel("Total Sales")
    ax.set_xlabel("Month")

    ax.legend(title="Year", title_fontsize=12, fontsize=10, loc='upper right')

    return fig

# Function to Display monthly total sales of customer from each category
def display_plots_monthly_sales_categories_per_customer(dict_df, customer, year):

    for key, val in dict_df.items(): 
        st.info(f"The chart showing {customer}`s monthly {key} sales in {year}🔻 ")
        # Seaborn style
        
        # Get total sales chart
        fig=get_barplot_of_category_client_monthly_sales(val, customer,key,year)

        # Displaying in Streamlit 
        st.pyplot(fig)
        st.markdown("")

##
### MAIN
##

if st.session_state["page"]=="start":
    st.header("Welcome to the app Shop Data Explorer ")
    st.markdown("In the app you will analyse data that was created for the shop", unsafe_allow_html=True)

    st.info("**If you want to check the app click button below *Continue***")
    if st.button("Continue"):
        st.session_state["page"]="main"
        st.rerun()

if st.session_state["page"]=="main":

    st.header("Welcome to data visualisation section 📊")
    st.session_state["mode"]=st.selectbox("Choose the mode below that you are interested in", [MODE_TOP,MODE_CLIENT, PRDUCT_INSIGHTS])
    
    # Top 3 mode
    if st.session_state["mode"]==MODE_TOP:
        st.info("Click tabs below to view sales performance by customer, product, and more 👇")

        #Customers Tab
        tab1,tab2,tab3,tab4,tab5=st.tabs(["Top Customers", "Top Products", "Top Categories", "Top Months","Top Countries"])

        # Sidebar options
        with st.sidebar:
            st.info("In this section you can choose filters that will be applied to the data that you analysing 👇")

            # Choosing which performence 
            st.session_state["performance_top"]=st.radio("Choose the TOP perfromence in Sales:", [BEST_PERFORMANCE, WORST_PERFORMANCE])
            performance=st.session_state["performance_top"]
        
            # Extracting data of the avaliable years in data
            year_top=get_years_filter_from_data()

            st.session_state["year_top"]=st.selectbox("📅 Choose the year to analyse", year_top, index=0)
            year=st.session_state["year_top"]

        
        with tab1:

            description=get_description_text_top_mode(performance, "Customers", "Total Sales", year)
            st.info(description)

            # Get df of the customers performance
            df_customers_top = get_top_perfromance_customers(performance, year, "")
            leaderboard_customers = leaderboard_html_inline(df_customers_top, "FullName","TotalSales","RankedClientsBySales",performance)
            st.markdown(leaderboard_customers, unsafe_allow_html=True)

        with tab2:
            
            description=get_description_text_top_mode(performance, "Products", "Total Sales", year)
            st.info(description)

            # Get df of the products performance
            df_products_top=get_top_perfromance_products(performance,year,"")
            leaderboard_products = leaderboard_html_inline(df_products_top,"ProductName", "TotalSales", "RankedProductsBySales", performance)
            st.markdown(leaderboard_products, unsafe_allow_html=True)

        with tab3:

            description=get_description_text_top_mode(performance, "Categories", "Total Sales", year)
            st.info(description)

            # Get df of the categories performance
            df_categories_top=get_top_perfromance_categories(performance,year,"")
            leaderboard_categories = leaderboard_html_inline(df_categories_top,"Category_Fixed", "TotalSales", "RankedCategorysBySales",performance)
            st.markdown(leaderboard_categories, unsafe_allow_html=True)

        with tab4:

            description=get_description_text_top_mode(performance, "Months", "Total Sales", year)
            st.info(description)

            # Get df of the month performance
            df_months_top=get_top_perfromance_moths(performance,year,"")
            leaderboard_months = leaderboard_html_inline(df_months_top,"Month_Maped", "TotalSales", "RankedMonthsBySales", performance)
            st.markdown(leaderboard_months, unsafe_allow_html=True)

        with tab5:
            description=get_description_text_top_mode(performance, "Countries", "Total Sales", year)
            st.info(description)

            # selected columns from tabs that are neded
            customers_select=get_customers_select(["CustomerID","Country"])
            orders_select=get_orders_select(["CustomerID","OrderDate","OrderID","strftime('%Y', OrderDate) AS Year"])
            orderdetails_select=get_orderdetails_select(["OrderID","Quantity","UnitPrice"])
            products_select=get_products_select(0)

            # selected columns from tabs to build where that is nedeed
            customers_filters=get_customers_where(customer=0,country=0)
            orders_filters=get_orders_where(year=year,month=0)
            orderdetails_filters=get_orderdetails_where(quantity=0,unitprice=0)
            products_filters=get_products_where(product=0,category=0)

            filters=[customers_filters,orders_filters,orderdetails_filters,products_filters]

            list_column_of_tabs=[customers_select,orders_select,orderdetails_select,products_select]

            dict_select_where=creating_dict_to_sql_query(list_column_of_tabs,filters)

            # Dictionary of dataframes with specyfic tab data
            dict_df_of_tabs=get_all_data_from_tables(dict_select_where)

            df_merged_top_countries=get_merged_top_performance_country(dict_df_of_tabs,performance)

            # Displaying leaderboard of countries
            leaderboard_countries=leaderboard_html_inline(df_merged_top_countries,"Country_mapped","Total_Sale", "RankedSales", performance)
            st.markdown(leaderboard_countries, unsafe_allow_html=True)
    # Mode client
    if st.session_state["mode"]==MODE_CLIENT:

        tab1, tab2, tab3, tab4 = st.tabs([
            "📆 Monthly Sales Overview",
            "📊 Category Sales",
            "📊 Category Share per Client",
            "🛒 Product Purchase Insights"
        ])

        with st.sidebar:

            st.info("Click tabs below to view sales performance by customer, product, and more 👇")

            # Get available years from data

            client_df=get_clients_from_db()
            st.session_state["client_one"]=st.selectbox("👤 Choose the clinent who you want to search deeply", client_df["Name"], index=0)
            client=st.session_state["client_one"]

            year=get_years_filter_from_data()
            st.session_state["year_client"]=st.selectbox("📅 Choose the year to analyse", year, index=0)
            year=st.session_state["year_client"]

        with tab1:

            customer_spec_df=get_specyfic_client_data(year,client)

            # Display visualization chart
            display_charts_monthly_sales_per_customer(customer_spec_df, client, year)
        
        with tab2:
            
            customers_select=get_customers_select(["CustomerID","Concat(FirstName,' ',LastName) AS Customer"])
            orders_select=get_orders_select(["CustomerID","OrderDate","OrderID","strftime('%Y', OrderDate) AS Year","round(strftime('%m', OrderDate),0) AS Month"])
            orderdetails_select=get_orderdetails_select(["OrderID","ProductID","Quantity","UnitPrice"])
            products_select=get_products_select(["ProductID","Category"])

            customers_filters=get_customers_where(customer=client,country=0)
            orders_filters=get_orders_where(year=year,month=0)
            orderdetails_filters=get_orderdetails_where(quantity=0,unitprice=0)
            products_filters=get_products_where(product=0,category=0)

            filters=[customers_filters,orders_filters,orderdetails_filters,products_filters]

            list_column_of_tabs=[customers_select,orders_select,orderdetails_select,products_select]

            dict_select_where=creating_dict_to_sql_query(list_column_of_tabs,filters)

            # Dictionary of dataframes with specyfic tab data
            dict_df_of_tabs=get_all_data_from_tables(dict_select_where)

            # Get dictionary of every category that client bought product from
            dict_df=get_dict_of_df_categories(dict_df_of_tabs)

            # display_plots_monthly_sales_categories_per_customer(dict_df,client,year)
            display_plots_monthly_sales_categories_per_customer(dict_df, client, year)

    # Mode products
    if st.session_state["mode"]==PRDUCT_INSIGHTS:
            with st.sidebar:
                st.markdown("In this section you can choose filters that will be applied to the data that you analysing 👇")

    
    


