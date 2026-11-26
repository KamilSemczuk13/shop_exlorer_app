# SQL queries for Top Performance and Deep Dive: Client

from config import (
    AVG_SALES,
    BEST_PERFORMANCE,
    CLEAN_DATA,
    MAX_SALE,
    MIN_SALE,
    RAW_DATA,
    TOTAL_SALES,
    WORST_PERFORMANCE,
)
from src.db import (
    creating_dict_to_sql_query,
    get_all_data_from_tables,
    get_customers_select,
    get_customers_where,
    get_df_from_db,
    get_orderdetails_select,
    get_orderdetails_where,
    get_orders_select,
    get_orders_where,
    get_products_select,
    get_products_where,
    get_string_of_years_to_filter,
    get_string_of_years_to_filter_v2,
    get_tables_for_version,
)
from src.transform import (
    get_dict_of_df_categories,
    get_map_month,
    get_mapped_categories_df,
    get_merged_top_performance_country,
    get_top_performance_categories_df,
    NULL_LABEL,
)


# Function to get available years in data (clean data has no None year)
def get_years_filter_from_data(data_version):

    if data_version==RAW_DATA:
        order_year=""
    else:
        order_year="Having OrderYear is not null"

    query=f'''

        SELECT 
            strftime('%Y', OrderDate) AS OrderYear
        FROM Orders
        Group by OrderYear
        {order_year};
    '''

    # Conecting to db
    data=get_df_from_db(query)

    return [year for year in data["OrderYear"]]


# Function to get years filters to sql query
def get_years_filter_to_query_sql(years):

    year=get_string_of_years_to_filter(years)

    year_group=f", OrderYear"
    year_exclude=f"AND OrderYear in {year} AND OrderYear is not null"

    return year_group, year_exclude


# Function to get raw years to filter
def get_years_filter_to_query_sql_raw(years):

    none_year=""
    year, none_exist=get_string_of_years_to_filter_v2(years)

    if none_exist==True:
        none_year=" OR OrderYear is Null"

    year_group=f", OrderYear"
    # Brackets so OR does not take rows of other customers
    year_having=f" AND (OrderYear in {year}{none_year})"

    return year_group, year_having


# Function to get years filters to sql query
# Year is in WHERE, because in HAVING (after GROUP BY customer) SQLite takes OrderDate of random order
# No HAVING: in clean data NULL sales are removed in WHERE (Quantity>0 AND UnitPrice>0), so TotalSales is never NULL
def get_years_filter_to_query_sql_v2(years):

    year=get_string_of_years_to_filter(years)

    return f"round(strftime('%Y', o.OrderDate)) in {year} AND round(strftime('%Y', o.OrderDate)) is not null"


# Function to get raw years to filter
def get_years_filter_to_query_sql_v2_raw(years):

    none_year=""
    year, none_exist=get_string_of_years_to_filter_v2(years)

    if none_exist==True:
        none_year="OR round(strftime('%Y', o.OrderDate)) is Null"

    return f"(round(strftime('%Y', o.OrderDate)) in {year} {none_year})"


# Function to get WHERE of top performance queries: years + correct values in clean data
def get_top_where_sql(year_where, data_version):

    conditions=[year_where]
    if data_version!=RAW_DATA:
        conditions.append("od.Quantity>0 AND od.UnitPrice>0")

    return "Where "+" AND ".join(conditions)


# Function to get filter of correct values (clean data has no Quantity <= 0 and price <= 0)
def get_valid_values_filter_sql(data_version):

    if data_version==RAW_DATA:
        return ""

    return "AND od.Quantity>0 AND od.UnitPrice>0"


# Function to get choosen metric of slaes directly to sql query
def get_metric_sale_sql(sale):

    sale_dict={
        TOTAL_SALES:"SUM",
        AVG_SALES:"AVG",
        MAX_SALE:"MAX",
        MIN_SALE:"MIN"
    }

    return sale_dict[sale]


# Function to get choosen performance directly to sql query
def get_performance_sql(performance):
    
    performance_dict={
        BEST_PERFORMANCE:"desc",
        WORST_PERFORMANCE:"asc"
    }

    return performance_dict[performance]


# Function to get customers performance from data
def get_top_perfromance_customers(performance, year, sale, data_version):

    #Get metric of sale
    sale=get_metric_sale_sql(sale)
     # Filtring per performance
    performance=get_performance_sql(performance)

    if data_version==RAW_DATA:
        year_where=get_years_filter_to_query_sql_v2_raw(year)
    else:
        year_where=get_years_filter_to_query_sql_v2(year)


    # Years and (in clean data) no values out of range
    valid_values=get_top_where_sql(year_where, data_version)

    query=f'''
        With RankedClientsTab AS(
            Select 
                round(strftime('%Y', o.OrderDate)) AS OrderYear,
                CONCAT(c.FirstName, " ",c.LastName) AS FullName,
                {sale}(od.UnitPrice * od.Quantity) AS TotalSales,
                rank() over(order by {sale}(od.UnitPrice * od.Quantity) {performance}) AS RankedClientsBySales
            From customers as c
            Inner join orders as o
                On c.CustomerID=o.CustomerID
            Inner join orderdetails as od
                On od.OrderID=o.OrderID
            {valid_values}
            Group by FullName
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
def get_top_perfromance_products(performance, year, sale,data_version):

    #Get metric of sale
    sale=get_metric_sale_sql(sale)
    # Filtring per performance
    performance=get_performance_sql(performance)

    if data_version==RAW_DATA:
        year_where=get_years_filter_to_query_sql_v2_raw(year)
    else:
        year_where=get_years_filter_to_query_sql_v2(year)

    # Years and (in clean data) no values out of range
    valid_values=get_top_where_sql(year_where, data_version)

    query=f'''
        With RankedProductsTab AS(
            Select 
                p.ProductName,
                {sale}(od.UnitPrice * od.Quantity) AS TotalSales,
                rank() over(order by {sale}(od.UnitPrice * od.Quantity) {performance}) AS RankedProductsBySales
            From products as p
            Inner join orderdetails as od
                On od.ProductID=p.ProductID
            Inner join orders as o
                On o.OrderID=od.OrderID
            {valid_values}
            Group by p.ProductName
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
def get_top_perfromance_categories(performance, year, sale, data_version):

    # Only filters of rows are in sql (years and correct values), mapping and grouping is in pandas
    if data_version==RAW_DATA:
        year_where=get_years_filter_to_query_sql_v2_raw(year)
    else:
        year_where=get_years_filter_to_query_sql_v2(year)

    # Years and (in clean data) no values out of range
    valid_values=get_top_where_sql(year_where, data_version)

    query=f'''
        Select 
            p.Category,
            od.UnitPrice * od.Quantity AS Sale
        From products as p
        Inner join orderdetails as od
            On od.ProductID=p.ProductID
        Inner join orders as o
            On o.OrderID=od.OrderID
        {valid_values};
    '''

    df_sales=get_df_from_db(query)

    # Category map (clean), metric of sale per category and rank of top 10
    df_categories_top=get_top_performance_categories_df(df_sales, performance, sale, data_version)
    return df_categories_top


def get_top_perfromance_moths(performance, year, sale, data_version):

    sale=get_metric_sale_sql(sale)
     # Filtring per performance
    performance=get_performance_sql(performance)

    if data_version==RAW_DATA:
        year_where=get_years_filter_to_query_sql_v2_raw(year)
    else:
        year_where=get_years_filter_to_query_sql_v2(year)

    # Years and (in clean data) no values out of range
    valid_values=get_top_where_sql(year_where, data_version)

    query=f'''
        With RankedMonthTab AS(
            Select 
                round(strftime('%m',OrderDate),0) AS Month,
                {sale}(od.UnitPrice * od.Quantity) AS TotalSales,
                rank() over(order by {sale}(od.UnitPrice * od.Quantity) {performance}) AS RankedMonthsBySales
            From products as p
            Inner join orderdetails as od
                On od.ProductID=p.ProductID
            Inner join orders as o
                On o.OrderID=od.OrderID
            {valid_values}
            Group by Month
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

    # Months are mapped to names in both versions (raw month from impossible date is "Unknown")
    df_months_top["Month_Maped"]=df_months_top["Month"].apply(get_map_month)

    return df_months_top


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


# Get info about client sales across the years
def get_client_data_sales_across_years(year, customer,data_version ):

    if data_version==RAW_DATA:
        year_exclude=get_years_filter_to_query_sql_raw(year)[1]
    else:
        year_exclude=get_years_filter_to_query_sql(year)[1]

    country=""

    # Clean data has no values out of range
    valid_values=get_valid_values_filter_sql(data_version)

    query=f'''

        Select
            Concat(c.FirstName, " ", c.LastName) AS Customer,
            round(strftime('%Y', o.OrderDate)) AS OrderYear,
            SUM(od.UnitPrice * od.Quantity) AS TotalSales
        From customers as c
        Inner join orders as o
            On c.CustomerID=o.CustomerID
        inner join orderdetails as od
            On O.OrderID=od.OrderID
        Where Concat(c.FirstName, " ", c.LastName)='{customer}' {year_exclude} {valid_values}
        Group by Customer, OrderYear
        
        
    '''
    #- having_year -
    # Conecting to db
    df_customer_spec=get_df_from_db(query)

    return df_customer_spec

# Get info about client moyhly sale
def get_specyfic_client_data(year, customer,data_version):

    if data_version==RAW_DATA:
        year_exclude=get_years_filter_to_query_sql_raw(year)[1]
    else:
        year_exclude=get_years_filter_to_query_sql(year)[1]

    # Clean data has no values out of range
    valid_values=get_valid_values_filter_sql(data_version)

    query=f'''
        With OrderTotals AS (
            Select
                o.OrderID,
                round(strftime('%Y', o.OrderDate)) AS OrderYear,
                round(strftime('%m', o.OrderDate), 0) AS Month,
                SUM(od.UnitPrice * od.Quantity) AS OrderTotal
            From customers as c
            Inner join orders as o On c.CustomerID=o.CustomerID
            Inner join orderdetails as od On o.OrderID=od.OrderID
            Where Concat(c.FirstName, " ", c.LastName)='{customer}' {year_exclude} {valid_values}
            Group by o.OrderID
        )
        Select
            OrderYear,
            Month,
            SUM(OrderTotal) AS TotalSales,   -- suma sprzedaży w miesiącu
            AVG(OrderTotal) AS AvgSales      -- średnia wartość zamówienia w miesiącu
        From OrderTotals
        Group by OrderYear, Month
    '''

    # Conecting to db
    df_customer_spec=get_df_from_db(query)

    # Clean data has no orders without month, in raw data month of impossible date is shown as NULL
    if data_version!=RAW_DATA:
        df_customer_spec = df_customer_spec.dropna(subset=["Month"])
    df_customer_spec["Month_normal"]=df_customer_spec["Month"].apply(get_map_month)
    df_customer_spec.loc[df_customer_spec["Month"].isna(), "Month_normal"]=NULL_LABEL
    df_customer_spec=df_customer_spec.sort_values("Month", ascending=True)

    return df_customer_spec


def get_categories_of_the_client(year, customer, data_version):

    categories_to_query="p.Category AS Category"

    query=f'''

        Select {categories_to_query}
        From customers as c
        Inner join orders as o
            On c.CustomerID=o.CustomerID
        inner join orderdetails as od
            On O.OrderID=od.OrderID
        inner join products as p
            On p.ProductID=od.ProductID
        Where Concat(c.FirstName, " ", c.LastName)='{customer}';
    '''

    # Conecting to db
    df_category_of_raw=get_df_from_db(query)

    df_category_of_cleint=df_category_of_raw

    if data_version==CLEAN_DATA:
        df_category_of_clean=get_mapped_categories_df(df_category_of_raw)
        df_category_of_cleint=df_category_of_clean

    return df_category_of_cleint


# Function to add orders with impossible date (NULL year) to where of orders, when None is chosen
# Raw data shows them, cleaning removes them from clean data
def get_dict_with_null_year(dict_of_cols_tabs, year):

    if None in year:
        dict_of_cols_tabs["orders"]["where"]=f"({dict_of_cols_tabs['orders']['where']} OR Year is null)"

    return dict_of_cols_tabs


# Function to get dict of selects and wheres to get countries data from tabs
def get_countries_select_where(year):

    # None can not be in sql "in (...)", it is added later as "Year is null"
    year_country=[year_country for year_country in year if  year_country is not None]

    # selected columns from tabs that are neded
    customers_select=get_customers_select(["CustomerID","Country"])
    orders_select=get_orders_select(["CustomerID","OrderDate","OrderID","round(strftime('%Y', OrderDate)) AS Year"])
    orderdetails_select=get_orderdetails_select(["OrderID","Quantity","UnitPrice"])
    products_select=get_products_select(0)

    # selected columns from tabs to build where that is nedeed
    customers_filters=get_customers_where(customer=0,country=0)
    orders_filters=get_orders_where(year=year_country,month=0)
    orderdetails_filters=get_orderdetails_where(quantity=0,unitprice=0)
    products_filters=get_products_where(product=0,category=0)

    filters=[customers_filters,orders_filters,orderdetails_filters,products_filters]

    list_column_of_tabs=[customers_select,orders_select,orderdetails_select,products_select]

    return get_dict_with_null_year(creating_dict_to_sql_query(list_column_of_tabs,filters), year)


# Function to get top countries df (data from every tab merged and ranked)
def get_top_performance_countries(performance, year, sale,data_version):

    # Dictionary of dataframes with specyfic tab data
    dict_df_of_tabs=get_all_data_from_tables(get_countries_select_where(year), data_version)

    return get_merged_top_performance_country(dict_df_of_tabs,performance, sale, data_version)


# Function to get top countries in raw and clean version, data is taken from db only once
def get_top_performance_countries_raw_and_clean(performance, year, sale):

    dict_df_raw=get_all_data_from_tables(get_countries_select_where(year), RAW_DATA)
    dict_df_clean=get_tables_for_version(dict_df_raw, CLEAN_DATA)

    df_clean=get_merged_top_performance_country(dict_df_clean,performance, sale,CLEAN_DATA)
    df_raw=get_merged_top_performance_country(dict_df_raw,performance, sale, RAW_DATA)

    return df_raw, df_clean


# Function to get dict of selects and wheres to get client categories data from tabs
def get_client_categories_select_where(client, year):

    # None can not be in sql "in (...)", it is added below as "Year is null"
    year_categories=[year_categories for year_categories in year if year_categories is not None]
    # get column to select from each tab
    customers_select=get_customers_select(["CustomerID","Concat(FirstName,' ',LastName) AS Customer"])
    orders_select=get_orders_select(["CustomerID","OrderDate","OrderID","round(strftime('%Y', OrderDate)) AS Year","round(strftime('%m', OrderDate),0) AS Month"])
    orderdetails_select=get_orderdetails_select(["OrderID","ProductID","Quantity","UnitPrice"])
    products_select=get_products_select(["ProductID","Category"])

    # get column with value to build where
    customers_filters=get_customers_where(customer=client,country=0)
    orders_filters=get_orders_where(year=year_categories,month=0)
    orderdetails_filters=get_orderdetails_where(quantity=0,unitprice=0)
    products_filters=get_products_where(product=0,category=0)

    filters=[customers_filters,orders_filters,orderdetails_filters,products_filters]

    list_column_of_tabs=[customers_select,orders_select,orderdetails_select,products_select]

    return get_dict_with_null_year(creating_dict_to_sql_query(list_column_of_tabs,filters), year)


# Function to get dictionary of client category sales (data from every tab merged)
def get_client_categories_dict(client, year, data_version):

    # Dictionary of dataframes with specyfic tab data
    dict_df_of_tabs=get_all_data_from_tables(get_client_categories_select_where(client, year), data_version)

    # Get dictionary of every category that client bought product from
    return get_dict_of_df_categories(dict_df_of_tabs, data_version)


# Function to get dictionaries of client category sales in raw and clean version, data is taken from db only once
def get_client_categories_dict_raw_and_clean(client, year):

    dict_df_raw=get_all_data_from_tables(get_client_categories_select_where(client, year), RAW_DATA)
    dict_df_clean=get_tables_for_version(dict_df_raw, CLEAN_DATA)

    dict_clean=get_dict_of_df_categories(dict_df_clean, CLEAN_DATA)
    dict_raw=get_dict_of_df_categories(dict_df_raw, RAW_DATA)

    return dict_raw, dict_clean
