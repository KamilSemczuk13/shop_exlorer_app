# Streamlit app - UI only, logic is in src/

import streamlit as st

from config import (
    AVG_SALES,
    BEST_PERFORMANCE,
    CLEAN_DATA,
    DB_MUTABLE,
    DB_ORIGINAL,
    DB_PATH,
    ERROR_TYPES,
    LOAD_YEARS,
    MAX_SALE,
    MIN_SALE,
    MODE_CLIENT,
    MODE_GENERATOR,
    MODE_TOP,
    MUTABLE_DB_PATH,
    PRDUCT_INSIGHTS,
    RAW_DATA,
    TOTAL_SALES,
    WORST_PERFORMANCE,
)
from src.db import get_string_of_years_to_filter, set_db_path
from src.generator import (
    ensure_mutable_db,
    generate_customers,
    generate_orders,
    generate_products,
    get_errors_log,
    get_errors_per_year,
    get_runs_log,
    get_tables_counts,
)
from src.transform import get_concated_categories_df
from src.queries import (
    get_client_categories_dict,
    get_client_data_sales_across_years,
    get_clients_from_db,
    get_specyfic_client_data,
    get_top_performance_countries,
    get_top_perfromance_categories,
    get_top_perfromance_customers,
    get_top_perfromance_moths,
    get_top_perfromance_products,
    get_years_filter_from_data,
)
from src.metrics import get_category_sets_raw_vs_clean
from src.charts import (
    display_accuracy_categories_raw_vs_clean,
    display_accuracy_raw_vs_clean,
    display_accuracy_values_raw_vs_clean,
    display_charts_monthly_sales_per_customer,
    display_errors_per_year_charts,
    display_plots_monthly_sales_categories_per_customer,
    display_plots_sales_years_per_customer,
    get_description_text_top_mode,
    leaderboard_html_inline,
)


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

if "data_version" not in st.session_state:
    st.session_state["data_version"]=""

if "db_version" not in st.session_state:
    st.session_state["db_version"]=DB_ORIGINAL


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

    # Choosing db that app is connected to
    with st.sidebar:
        st.session_state["db_version"]=st.radio("🗄️ Choose the database", [DB_ORIGINAL, DB_MUTABLE])

    if st.session_state["db_version"]==DB_MUTABLE:
        # Mutable db is created as copy of original when it is used first time
        ensure_mutable_db(DB_PATH, MUTABLE_DB_PATH)
        set_db_path(MUTABLE_DB_PATH)
    else:
        set_db_path(DB_PATH)

    st.session_state["mode"]=st.selectbox("Choose the mode below that you are interested in", [MODE_TOP,MODE_CLIENT, MODE_GENERATOR, PRDUCT_INSIGHTS])
    
    # Top 3 mode
    if st.session_state["mode"]==MODE_TOP:
        st.info("Click tabs below to view sales performance by customer, product, and more 👇")

        #Customers Tab
        tab1,tab2,tab3,tab4,tab5=st.tabs(["Top Customers", "Top Products", "Top Categories", "Top Months","Top Countries"])

        # Sidebar options
        with st.sidebar:
            st.info("In this section you can choose filters that will be applied to the data that you analysing 👇")

            st.session_state["data_version"]=st.radio("📊 Choose the version of data to analyse", [CLEAN_DATA, RAW_DATA])
            data_version=st.session_state["data_version"]

            # Choosing which performence 
            st.session_state["performance_top"]=st.radio("Choose the TOP perfromence in Sales:", [BEST_PERFORMANCE, WORST_PERFORMANCE])
            performance=st.session_state["performance_top"]
        
            # Extracting data of the avaliable years in data
        
            type_of_sale=st.radio("📊 Select metric:",[TOTAL_SALES,AVG_SALES,MAX_SALE,MIN_SALE])

            year_top=get_years_filter_from_data(data_version)

            st.session_state["year_top"]=st.multiselect("📅 Choose the year to analyse", year_top, default=year_top[-1])
            year=st.session_state["year_top"]

        years_to_desc=get_string_of_years_to_filter(year)

        # Raw data is compared with clean data, clean data has no None years
        is_raw=data_version==RAW_DATA
        year_clean=[year_clean for year_clean in year if year_clean is not None]

        with tab1:

            description=get_description_text_top_mode(performance, "Customers", "Total Sales", years_to_desc)
            st.info(description)

            # Get df of the customers performance
            df_customers_top = get_top_perfromance_customers(performance, year, type_of_sale, data_version)

            if is_raw:
                df_customers_clean=get_top_perfromance_customers(performance, year_clean, type_of_sale, CLEAN_DATA)
                display_accuracy_raw_vs_clean(df_customers_clean, df_customers_top, "FullName", "FullName", "RankedClientsBySales")

            leaderboard_customers = leaderboard_html_inline(df_customers_top, "FullName","TotalSales","RankedClientsBySales",performance)
            st.markdown(leaderboard_customers, unsafe_allow_html=True)

        with tab2:
            
            description=get_description_text_top_mode(performance, "Products", "Total Sales", years_to_desc)
            st.info(description)

            # Get df of the products performance
            df_products_top=get_top_perfromance_products(performance,year,type_of_sale, data_version)

            if is_raw:
                df_products_clean=get_top_perfromance_products(performance, year_clean, type_of_sale, CLEAN_DATA)
                display_accuracy_raw_vs_clean(df_products_clean, df_products_top, "ProductName", "ProductName", "RankedProductsBySales")

            leaderboard_products = leaderboard_html_inline(df_products_top,"ProductName", "TotalSales", "RankedProductsBySales", performance)
            st.markdown(leaderboard_products, unsafe_allow_html=True)

        with tab3:

            description=get_description_text_top_mode(performance, "Categories", "Total Sales", years_to_desc)
            st.info(description)

            # Get df of the categories performance
            df_categories_top=get_top_perfromance_categories(performance,year,type_of_sale, data_version)

            if is_raw:
                df_categories_clean=get_top_perfromance_categories(performance, year_clean, type_of_sale, CLEAN_DATA)
                display_accuracy_raw_vs_clean(df_categories_clean, df_categories_top, "Category_Fixed", "Category_Fixed", "RankedCategorysBySales")

            leaderboard_categories = leaderboard_html_inline(df_categories_top,"Category_Fixed", "TotalSales", "RankedCategorysBySales",performance)
            st.markdown(leaderboard_categories, unsafe_allow_html=True)

        with tab4:

            description=get_description_text_top_mode(performance, "Months", "Total Sales", years_to_desc)
            st.info(description)

            # Get df of the month performance
            df_months_top=get_top_perfromance_moths(performance,year,type_of_sale, data_version)

            if is_raw:
                # Clean months are mapped to names, so compare month numbers
                df_months_clean=get_top_perfromance_moths(performance, year_clean, type_of_sale, CLEAN_DATA)
                display_accuracy_raw_vs_clean(df_months_clean, df_months_top, "Month", "Month_Maped", "RankedMonthsBySales")

            leaderboard_months = leaderboard_html_inline(df_months_top,"Month_Maped", "TotalSales", "RankedMonthsBySales", performance)
            st.markdown(leaderboard_months, unsafe_allow_html=True)

        with tab5:
            description=get_description_text_top_mode(performance, "Countries", "Total Sales", years_to_desc)
            st.info(description)

            df_merged_top_countries=get_top_performance_countries(performance, year, data_version)

            if is_raw:
                df_countries_clean=get_top_performance_countries(performance, year, CLEAN_DATA)
                display_accuracy_raw_vs_clean(df_countries_clean, df_merged_top_countries, "Country_mapped", "Country_mapped", "RankedSales")

            # Displaying leaderboard of countries
            leaderboard_countries=leaderboard_html_inline(df_merged_top_countries,"Country_mapped","Total_Sale", "RankedSales", performance)
            st.markdown(leaderboard_countries, unsafe_allow_html=True)
    # Mode client
    if st.session_state["mode"]==MODE_CLIENT:

        tab1, tab2 = st.tabs([
            "📆 Monthly Sales Overview",
            "📊 Category Sales",
            # "📊 Category Share per Client",
            # "🛒 Product Purchase Insights"
        ])

        with st.sidebar:

            st.info("Click tabs below to view sales performance by customer, product, and more 👇")

            # Get available years from data

            st.session_state["data_version"]=st.radio("📊 Choose the version of data to analyse", [CLEAN_DATA, RAW_DATA])
            data_version=st.session_state["data_version"]

            year=get_years_filter_from_data(data_version)
            st.session_state["year_client"]=st.multiselect("📅 Choose the year to analyse", year, year[-1])
            year=st.session_state["year_client"]

            client_df=get_clients_from_db()
            st.session_state["client_one"]=st.selectbox("👤 Choose the clinent who you want to search deeply", client_df["Name"], index=0)
            client=st.session_state["client_one"]

        year_to_desc=get_string_of_years_to_filter(year)

        # Raw data is compared with clean data, clean data has no None years
        is_raw=data_version==RAW_DATA
        year_clean=[year_clean for year_clean in year if year_clean is not None]

        with tab1:

            client_sales_df=get_client_data_sales_across_years(year,client, data_version)

            if is_raw:
                client_sales_clean_df=get_client_data_sales_across_years(year_clean, client, CLEAN_DATA)
                display_accuracy_values_raw_vs_clean(client_sales_clean_df, client_sales_df, ["OrderYear"], "TotalSales")

            display_plots_sales_years_per_customer(client_sales_df,"TotalSales",client,year_to_desc)

            customer_spec_df=get_specyfic_client_data(year,client, data_version)

            customer_spec_clean_df=get_specyfic_client_data(year_clean, client, CLEAN_DATA) if is_raw else None

            display_charts_monthly_sales_per_customer(customer_spec_df, client, year_to_desc, customer_spec_clean_df)


        with tab2:

            dict_df=get_client_categories_dict(client, year, data_version)

            # Comparison only for raw data (clean data has nothing to compare with)
            dict_sets=None
            if is_raw:
                df_categories_clean=get_concated_categories_df(get_client_categories_dict(client, year, CLEAN_DATA))
                df_categories_raw=get_concated_categories_df(dict_df)

                display_accuracy_categories_raw_vs_clean(df_categories_clean, df_categories_raw)

                # Sets per category to show comparison above every chart
                dict_sets=get_category_sets_raw_vs_clean(df_categories_clean, df_categories_raw)

            # display_plots_monthly_sales_categories_per_customer(dict_df,client,year)
            display_plots_monthly_sales_categories_per_customer(dict_df, client, year_to_desc, dict_sets)

    # Mode generator
    if st.session_state["mode"]==MODE_GENERATOR:

        # Generator always inserts records into mutable db, original db is never changed
        ensure_mutable_db(DB_PATH, MUTABLE_DB_PATH)

        st.info("Generator inserts new records into **🧪 Mutable DB**. Part of the records is polluted with chosen errors, every error is saved in table *Data_Quality_Errors* 👇")

        if st.session_state["db_version"]==DB_ORIGINAL:
            st.warning(f"You are connected to **{DB_ORIGINAL}**. Choose **{DB_MUTABLE}** in the sidebar to analyse generated records.")

        col1, col2=st.columns(2)
        with col1:
            n_customers=st.slider("👤 Number of customers", 1, 50, 5)
            n_products=st.slider("📦 Number of products", 1, 30, 5)
            n_orders=st.slider("🛒 Number of orders", 1, 200, 20)
        with col2:
            # Chunk of data is delivered in chosen year, dates of records are in this year
            load_year=st.selectbox("📅 Year of data delivery", LOAD_YEARS, index=LOAD_YEARS.index(2025))
            pollution=st.slider("☣️ Pollution level (% of polluted records)", 0, 100, 20)
            st.markdown("**Types of inserted errors:**")
            error_types=[error_type for error_type in ERROR_TYPES if st.checkbox(error_type, value=True)]

        btn1, btn2, btn3=st.columns(3)
        generate_clicked={
            "customers":btn1.button("Generate customers", use_container_width=True),
            "products":btn2.button("Generate products", use_container_width=True),
            "orders":btn3.button("Generate orders", use_container_width=True),
        }

        generators={
            "customers":(generate_customers, n_customers),
            "products":(generate_products, n_products),
            "orders":(generate_orders, n_orders),
        }

        for name, clicked in generate_clicked.items():
            if not clicked:
                continue

            generator, n=generators[name]
            try:
                result=generator(MUTABLE_DB_PATH, n, pollution/100, error_types, load_year=load_year)
                st.success(f"✅ Run {result['run_id']} ({load_year}): inserted {result['inserted']} {name}, polluted values: {result['polluted']}")
            except ValueError as ex:
                st.error(f"❌ {ex}")

        # State of mutable db after generating
        st.subheader("📋 State of Mutable DB")

        col1, col2=st.columns(2)
        with col1:
            st.markdown("**Rows in tables**")
            st.dataframe(get_tables_counts(MUTABLE_DB_PATH), hide_index=True, use_container_width=True)

        df_errors=get_errors_log(MUTABLE_DB_PATH)
        with col2:
            st.markdown("**Inserted errors**")
            if df_errors.empty:
                st.caption("No errors inserted yet")
            else:
                df_errors_count=df_errors.groupby(["TableName","ErrorType"]).size().reset_index(name="Count")
                st.dataframe(df_errors_count, hide_index=True, use_container_width=True)

        # Errors in every year of data delivery
        st.subheader("📈 Errors per year of data delivery")
        df_runs=get_runs_log(MUTABLE_DB_PATH)
        df_years=get_errors_per_year(df_runs)

        display_errors_per_year_charts(df_errors, df_years)

        if not df_years.empty:
            st.dataframe(df_years, hide_index=True, use_container_width=True)

        if not df_runs.empty:
            with st.expander(f"Show log of generator runs ({len(df_runs)})"):
                st.dataframe(df_runs, hide_index=True, use_container_width=True)

        if not df_errors.empty:
            with st.expander(f"Show log of inserted errors ({len(df_errors)})"):
                st.dataframe(df_errors, hide_index=True, use_container_width=True)

    # Mode products
    if st.session_state["mode"]==PRDUCT_INSIGHTS:
            with st.sidebar:
                st.markdown("In this section you can choose filters that will be applied to the data that you analysing 👇")
