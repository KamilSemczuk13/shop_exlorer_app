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


### Cleaning data funtions and maniplualzing data

# Cleaning data
def cleaning_data(df, col):

    return df[
        (df[col].notna()) & (df[col].astype(str).str.strip() != "") &
        (df[col].astype(str).str.strip().str.lower() != "null") & 
        (df[col].astype(str).str.strip().str.lower() != "none")
    ]

# Get clean df from data
def get_cleaned_data(df):

    for col in df.columns:
        df=cleaning_data(df, col)

    return df

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
        year_having=f"Having TotalSales is not null and OrderYear is not null and OrderYear ='{year}'"

    return year_group, year_having
    

# Function to get customers performance from data
def get_top_perfromance_customers(performance, year, country):

     # Filtring per performance
    if performance == BEST_PERFORMANCE:
        performance="desc"
    else: 
        performance="asc"

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
            {year_having}
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
    if performance == BEST_PERFORMANCE:
        performance="desc"
    else: 
        performance="asc"

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
            {year_having}
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
    if performance == BEST_PERFORMANCE:
        performance="desc"
    else: 
        performance="asc"

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
            {year_having}
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
    if performance == BEST_PERFORMANCE:
        performance="desc"
    else: 
        performance="asc"

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
            {year_having}
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
    # performance_dict={
    #     BEST_PERFORMANCE:"Performance from the best",
    #     WORST_PERFORMANCE:"Performance from the worst" 
    # }
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
        Having Concat(c.FirstName, " ", c.LastName)="{customer}"
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

# Get columns from customer table
def get_columns_of_customers(year, customer):
    
    year_group, year_having=get_years_filter_to_query_sql(year)
    country=""

    query=f'''

        Select
            *
        customers
    '''

    # Conecting to db
    df_customers_columns=get_df_from_db(query)
    df_customers_columns_cleaned=get_cleaned_data(df_customers_columns)
    return df_customers_columns_cleaned

# Get column from order table
def get_columns_of_orders(year, customer):
    
    year_group, year_having=get_years_filter_to_query_sql(year)
    country=""

    query=f'''

        Select
            *
        orders
    '''

    # Conecting to db
    df_orders_columns=get_df_from_db(query)
    df_orders_columns_cleaned=get_cleaned_data(df_orders_columns)
    return df_orders_columns_cleaned


def get_columns_of_orderdetails(year, customer):
    
    year_group, year_having=get_years_filter_to_query_sql(year)
    country=""

    query=f'''

        Select
            *
        orderdetails
    '''

    # Conecting to db
    df_orders_columns=get_df_from_db(query)
    df_orders_columns_cleaned=get_cleaned_data(df_orders_columns)
    return df_orders_columns_cleaned



### FUNCTIONS to visualise data

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
def get_total_monthy_sales_chart(df, customer):
    sns.set_style("whitegrid")  
    sns.set_palette("tab10")    

    # creating plot
    fig, ax = plt.subplots(figsize=(10,5))
    sns.lineplot(
        x="Month_normal",
        y="TotalSales",
        hue="OrderYear",
        data=df,
        marker="o",   
        ax=ax
    )

    # Tittle and series osi
    ax.set_title(f"Monthly Total Sales of {customer}", fontsize=16)
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Total Sales", fontsize=12)

    # adding legend
    ax.legend(title="Year", title_fontsize=12, fontsize=10, loc='upper left')

    return fig

# Get average monthly sales chart
def get_average_monthy_sales_chart(df, customer):

    # Seaborn style
    sns.set_style("whitegrid")  
    sns.set_palette("tab10")    

    # creating plot
    fig, ax = plt.subplots(figsize=(10,5))
    sns.lineplot(
        x="Month_normal",
        y="AvgSales",
        hue="OrderYear",
        data=df,
        marker="o",    
        ax=ax
    )

    # Tittle and series osi
    ax.set_title(f"Monthly Average Sales of {customer}", fontsize=16)
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Total Sales", fontsize=12)

    # adding legend
    ax.legend(title="Year", title_fontsize=12, fontsize=10, loc='upper left')

    return fig


# Function to Display average an total sales of customer 
def display_charts_monthly_sales_per_customer(df, customer):

    st.info(f"The chart showing monthly Sales of {customer} 🔻")
    # Seaborn style
    
    # Get total sales chart
    fig=get_total_monthy_sales_chart(df,customer)

    # Displaying in Streamlit 
    st.pyplot(fig)
    st.markdown("")

    st.info(f"The chart showing monthly Average Sales of {customer} 🔻")

    # Get average sales 
    fig=get_average_monthy_sales_chart(df,customer)

    # Displaying in Streamlit 
    st.pyplot(fig)


##
### MAIN
##

if st.session_state["page"]=="start":
    st.header("Welcome to the app Shop Data Explorer📊🔍 ")
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
        tab1,tab2,tab3,tab4=st.tabs(["Top Customers", "Top Products", "Top Categories", "Top Months"])

        # Sidebar options
        with st.sidebar:
            st.info("In this section you can choose filters that will be applied to the data that you analysing 👇")

            # Choosing which performence 
            st.session_state["performance_top"]=st.radio("Choose the TOP perfromence in Sales:", [BEST_PERFORMANCE, WORST_PERFORMANCE])
            performance=st.session_state["performance_top"]
        
            # Extracting data of the avaliable years in data
            year_top=get_years_filter_from_data()

            st.session_state["year_top"]=st.selectbox("Choose the year to analyse", year_top, index=0)
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

    # Mode client
    if st.session_state["mode"]==MODE_CLIENT:

        client_df=get_clients_from_db()
        st.session_state["client_one"]=st.selectbox("Choose the clinent who you want to search deeply", client_df["Name"], index=0)
        client=st.session_state["client_one"]

        tab1, tab2, tab3 = st.tabs([
            "📆 Monthly Sales Overview",
            "📊 Category Share per Client",
            "🛒 Product Purchase Insights"
        ])
        with st.sidebar:

            st.info("Click tabs below to view sales performance by customer, product, and more 👇")

            # Get available years from data
            year=get_years_filter_from_data()
            st.session_state["year_client"]=st.selectbox("Choose the year to analyse", year, index=0)
            year=st.session_state["year_client"]
        with tab1:

            customer_spec_df=get_specyfic_client_data(year,client)

            # Display visualization chart
            display_charts_monthly_sales_per_customer(customer_spec_df, client)
        
        with tab2:

            # Get Categories of client
            df_categories_of_client=get_categories_of_the_client(year, client)

            st.dataframe(df_categories_of_client)

    # Mode products
    if st.session_state["mode"]==PRDUCT_INSIGHTS:
            with st.sidebar:
                st.markdown("In this section you can choose filters that will be applied to the data that you analysing 👇")

    
    


