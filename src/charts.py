# Visualisation: leaderboards, charts and accuracy info bars in Streamlit

import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt

from config import (
    AVG_SALES,
    BEST_PERFORMANCE,
    MAX_SALE,
    MIN_SALE,
)
from src.transform import get_monthly_chart_values
from src.metrics import get_accuracy_raw_vs_clean, get_accuracy_values_raw_vs_clean, get_category_set_key


# Description of action of the leaderboard
def get_description_text_top_mode(performance, tab, type_of_sales, years):
    
    text=f"The LEADERBOARD below is showing you {performance}  *{tab}* in **{type_of_sales}** in **{years}**"

    return text


# Display info bar with accuracy and comparison table
def display_accuracy_info(matches, total, df_comparison, what="positions", show_table=True):

    if total==0:
        st.info("🎯 Accuracy raw vs clean: no data to compare")
        return

    accuracy=matches/total*100
    st.info(f"🎯 Accuracy raw vs clean: **{matches}/{total}** {what} match (**{accuracy:.2f}%**)")

    if show_table:
        with st.expander("Show comparison clean vs raw"):
            st.dataframe(df_comparison, use_container_width=True)


# Display total accuracy of client categories (every category together)
def display_accuracy_categories_raw_vs_clean(df_clean, df_raw):

    matches, total, df_comparison=get_accuracy_values_raw_vs_clean(df_clean, df_raw, ["Category_mapped","Year","Month"], "Total_Sale_Category")
    display_accuracy_info(matches, total, df_comparison, "values", show_table=False)


# Display accuracy of one category set
def display_accuracy_category_set(df_set_clean, df_set_raw):

    display_accuracy_values_raw_vs_clean(df_set_clean, df_set_raw, ["Category_mapped","Year","Month"], "Total_Sale_Category")


# Display accuracy of raw data compared to clean data
def display_accuracy_raw_vs_clean(df_clean, df_raw, clean_col, raw_col, rank_col):

    matches, total, df_comparison=get_accuracy_raw_vs_clean(df_clean, df_raw, clean_col, raw_col, rank_col)
    display_accuracy_info(matches, total, df_comparison)


# Display accuracy of raw values compared to clean values
def display_accuracy_values_raw_vs_clean(df_clean, df_raw, key_cols, value_col):

    matches, total, df_comparison=get_accuracy_values_raw_vs_clean(df_clean, df_raw, key_cols, value_col)
    display_accuracy_info(matches, total, df_comparison, "values")


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


# Function to Display total sales of customer across the years from each category
def display_plots_sales_years_per_customer(df, type_of_sales,customer, year):

    sales_dict={
        "TotalSales":"Total Sale",
        AVG_SALES:"Average Sale",
        MAX_SALE:"Maximal Sale",
        MIN_SALE:"Minimal Sale"

    }
    # sns.set_style("whitegrid")

    # Reset color cycle to avoid modulo by zero
    plt.rcParams['axes.prop_cycle'] = plt.cycler('color', ['b', 'g', 'r', 'c', 'm', 'y', 'k'])
    sns.set_palette("pastel")

    # Tworzenie wykresu
    fig, ax = plt.subplots(figsize=(8, 3))  # szerszy, niższy kontener

    sns.barplot(
        x="OrderYear",
        y="TotalSales",
        data=df,
        ax=ax,
        dodge=True,         # rozdziela słupki dla hue
        width=0.6,  # zmniejsza szerokość słupków
    )

    st.info(f"The chart showing {sales_dict[type_of_sales]} of {customer} in {year}🔻 ")

    ax.set_title(f"{sales_dict[type_of_sales]} of {customer} in {year}", fontsize=14)
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel(f"{sales_dict[type_of_sales]}", fontsize=10)

    # Etykiety osi X — mniejsze i obrócone
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, fontsize=8)


    # Zmniejszenie marginesu dolnego
    plt.subplots_adjust(bottom=0.25)

    st.pyplot(fig)


# Get monthly total sales chart
def get_monthly_sales_chart(df, type_of_sales, customer,year):

    sales_desc={
        "TotalSales":"Total Sales",
        "AvgSales":"Anerage Sales"
    }



    # Tworzenie wykresu
    fig, ax = plt.subplots(figsize=(8, 3))  # szerszy, niższy kontener

    sns.barplot(
        x="Month_normal",
        y=f"{type_of_sales}",
        hue="OrderYear",
        data=df,
        ax=ax,
        dodge=True,         # rozdziela słupki dla hue
        width=0.6,  # zmniejsza szerokość słupków
    )

    # Tytuł i etykiety osi
    ax.set_title(f"Monthly {sales_desc[type_of_sales]} of {customer} in {year}", fontsize=14)
    ax.set_xlabel("Month", fontsize=10)
    ax.set_ylabel(f"{sales_desc[type_of_sales]}", fontsize=10)

    # Etykiety osi X — mniejsze i obrócone
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, fontsize=8)

    # Zmniejszenie marginesu dolnego
    plt.subplots_adjust(bottom=0.25)

    return fig


# Function to Display average and total sales of customer
def display_charts_monthly_sales_per_customer(df, customer, year, df_clean=None):

    st.info(f"The chart showing monthly Sales of {customer} in {year}🔻 ")
    # Seaborn style

    # Accuracy only when raw data is compared with clean data
    if df_clean is not None:
        df_chart_raw=get_monthly_chart_values(df)
        df_chart_clean=get_monthly_chart_values(df_clean)
        display_accuracy_values_raw_vs_clean(df_chart_clean, df_chart_raw, ["OrderYear","Month"], "TotalSales")

    # Get total sales chart
    fig=get_monthly_sales_chart(df, "TotalSales",customer, year)

    # Displaying in Streamlit 
    st.pyplot(fig)
    st.markdown("")

    st.info(f"The chart showing monthly Average Sales of {customer} in {year}🔻")

    if df_clean is not None:
        display_accuracy_values_raw_vs_clean(df_chart_clean, df_chart_raw, ["OrderYear","Month"], "AvgSales")

    # Get average sales 
    fig=get_monthly_sales_chart(df,"AvgSales",customer,year)

    # Displaying in Streamlit 
    st.pyplot(fig)


# Create plot of sales of the categories that customer bought product from
def get_barplot_of_category_client_monthly_sales(df,customer,category,year):

    fig, ax=plt.subplots(figsize=(5,2))

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
def display_plots_monthly_sales_categories_per_customer(dict_df, customer, year, dict_sets=None):

    # Sets already shown ("Electronics" and "electronics" charts are in the same set)
    shown_sets=[]

    for key, val in dict_df.items():
        st.info(f"The chart showing {customer}`s monthly {key} sales in {year}🔻 ")
        # Seaborn style

        # Accuracy only when raw data is compared with clean data
        if dict_sets is not None:
            set_key=get_category_set_key(key)
            set_name, df_set_clean, df_set_raw=dict_sets[set_key]

            if set_key in shown_sets:
                st.caption(f"🎯 Comparison of **{set_name}** set is shown above")
            else:
                shown_sets.append(set_key)
                display_accuracy_category_set(df_set_clean, df_set_raw)

        # Get total sales chart
        fig=get_barplot_of_category_client_monthly_sales(val, customer,key,year)

        # Displaying in Streamlit
        st.pyplot(fig)
        st.markdown("")


# Display charts of inserted errors in every year of data delivery
def display_errors_per_year_charts(df_errors, df_years):

    df_errors=df_errors.dropna(subset=["LoadYear"]).astype({"LoadYear":int})

    if df_errors.empty or df_years.empty:
        st.caption("No errors with year of data delivery yet")
        return

    # Number of errors per year and error type
    fig, ax=plt.subplots(figsize=(8, 3))
    df_count=df_errors.groupby(["LoadYear","ErrorType"]).size().reset_index(name="Errors")
    sns.barplot(data=df_count, x="LoadYear", y="Errors", hue="ErrorType", ax=ax)

    ax.set_title("Inserted errors per year of data delivery", fontsize=14)
    ax.set_xlabel("Year of data delivery", fontsize=10)
    ax.set_ylabel("Errors", fontsize=10)
    ax.legend(title="Error type", fontsize=7, title_fontsize=8, loc="upper left", bbox_to_anchor=(1, 1))

    st.pyplot(fig)

    # Share of polluted rows, because number of inserted rows can be different every year
    fig, ax=plt.subplots(figsize=(8, 3))
    sns.barplot(data=df_years, x="LoadYear", y="PollutedPercent", ax=ax, width=0.6)

    ax.set_title("Polluted rows per year of data delivery", fontsize=14)
    ax.set_xlabel("Year of data delivery", fontsize=10)
    ax.set_ylabel("Polluted rows %", fontsize=10)
    ax.bar_label(ax.containers[0], fmt="%.1f%%", fontsize=8)

    st.pyplot(fig)
