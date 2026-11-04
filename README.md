# 🛒 Shop Data Explorer
---
Explore online shop sales data with an interactive **Streamlit app**. Analyze customer, product, and category performance, and track monthly trends.

## 🚀 Features

- Filter sales data by year(s), customers, sales metrics, performance   
- Analyze top/worst customers, products, and categories  
- Visualize monthly and overall sales trends  

## 🧰 Tech Stack

Python, SQLite, Streamlit, Pandas, Matplotlib, Seaborn

## 📁 Project Structure

```
Shop_app_1/
├── app.py              # Streamlit UI (main)
├── config.py           # static variables (DB path, modes, labels)
├── data/
│   ├── db_shop.db          # original SQLite database (never changed)
│   └── db_shop_mutable.db  # copy of original, generator inserts records here (not in git)
├── src/
│   ├── db.py           # connection + building SELECT / WHERE
│   ├── queries.py      # SQL queries: top performance, client deep dive
│   ├── transform.py    # mapping months/countries/categories, cleaning, merging
│   ├── metrics.py      # accuracy raw vs clean data
│   ├── generator.py    # inserting generated records with polluted values
│   └── charts.py       # leaderboards, charts, accuracy info
├── tests/              # pytest: unit tests + integration tests on db
└── requirements.txt
```

## ▶️ Run

```
pip install -r requirements.txt
streamlit run app.py
```

## 🧪 Tests

```
pytest
```

## 📅 Development Highlights

- Data extraction and cleaning using SQL + Pandas  
- Customer/product/category rankings and leaderboard creation  
- Interactive visualizations in Streamlit  
- Modular functions for reusable ETL and analytics  

## 📸 Screenshot

### 📝 Top Customers / Products / Categories
![Shop Data Explorer Screenshot](https://github.com/KamilSemczuk13/zdj_portfolio/blob/main/Shop_exp/Zrzut%20ekranu%202025-09-14%20163004.png?raw=true)
*Interactive dashboards for exploring sales performance.*

## 👉 Portfolio

Learn more about this project: [Shop Data Explorer](https://kamilsemczuk13.github.io/ds_portfolio_ENG/Data_Engineering/Shop/)


My portfolio with every project: [My Portfolio](https://kamilsemczuk13.github.io/ds_portfolio_ENG/)
