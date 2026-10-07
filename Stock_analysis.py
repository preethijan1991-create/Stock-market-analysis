import os
import yaml
import pandas as pd
import matplotlib.pyplot as plt
import glob
from sqlalchemy import create_engine
import streamlit as st

folder_path = "C:/Users/Shiva S R/OneDrive/Desktop/Stack"

yaml_files = [f for f in os.listdir(folder_path) if f.endswith(('.yaml', '.yml'))]

data_list = []

for file in yaml_files:
    file_path = os.path.join(folder_path, file)
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)   
        data_list.append(data)   

df = pd.DataFrame(data_list)



new_rows = []
for i in range(len(df)):
    row = df.iloc[i]   # one row
    # Each cell is a dict → convert to DataFrame row
    expanded = pd.DataFrame(list(row), columns=['Ticker','close','date','high','low','month','open','volume'])
    expanded['row_index'] = i   # keep track of original row
    new_rows.append(expanded)

final_df = pd.concat(new_rows, ignore_index=True)


final_df.to_csv('C:/Users/Shiva S R/OneDrive/Desktop/Stack.csv', index=False)

tickers = final_df['Ticker'].unique()


# Read all CSV files into one DataFrame

files = glob.glob("C:/Users/Shiva S R/OneDrive/Desktop/Stock/*.csv")  # <-- use *.csv
df_list = []

for file in files:
    temp_df = pd.read_csv(file)
    df_list.append(temp_df)

# Combine all files
data = pd.concat(df_list, ignore_index=True)


# VOLATILITY ANALYSIS

data["date"] = pd.to_datetime(data["date"])
data = data.sort_values(["Ticker", "date"])

data["Daily_Return"] = data.groupby("Ticker")["close"].pct_change()

volatility = data.groupby("Ticker")["Daily_Return"].std().reset_index()
volatility.columns = ["Ticker", "Volatility"]

# Top 10 most volatile stocks
volatility_df = volatility.sort_values("Volatility", ascending=False).head(10)



#  VISUALISATION

plt.figure(figsize=(10,6))
plt.bar(volatility_df["Ticker"], volatility_df["Volatility"], color="red")
plt.title("Top 10 Most Volatile Stocks (Past Year)")
plt.xlabel("Stock Ticker")
plt.ylabel("Volatility (Std Dev of Daily Returns)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# CUMULATIVE RETURN

data['date'] = pd.to_datetime(data['date'])
data = data.sort_values(by=['Ticker', 'date'])

data['daily_return'] = data.groupby('Ticker')['close'].pct_change()

data['cumulative_return'] = (1 + data['daily_return']).groupby(data['Ticker']).cumprod()

final_returns = data.groupby('Ticker')['cumulative_return'].last().sort_values(ascending=False)
cumulative_return_df = final_returns.head(5).index


# VISUALISATION

plt.figure(figsize=(12,6))
for ticker in cumulative_return_df:
    subset = data[data['Ticker'] == ticker]
    plt.plot(subset['date'], subset['cumulative_return'], label=ticker)

plt.title("Cumulative Return of Top 5 Performing Stocks")
plt.xlabel("Date")
plt.ylabel("Cumulative Return")
plt.legend()
plt.tight_layout()
plt.show()


# SECTOR WISE

sector_df = pd.read_csv("C:/Users/Shiva S R/OneDrive/Desktop/Stock/sector/Sector.csv")

data['date'] = pd.to_datetime(data['date'])
data = data.sort_values(by=['Ticker', 'date'])

# Step 1: Calculate Yearly Return safely
yearly_returns = (
    data.groupby("Ticker")
    .apply(lambda x: (x["close"].dropna().iloc[-1] - x["close"].dropna().iloc[0]) / x["close"].dropna().iloc[0]
    )
    .reset_index(name="Yearly_Return")
)

# Step 2: Merge sector info
yearly_returns = yearly_returns.merge(sector_df, on="Ticker", how="inner")

# Step 3: Drop NaN values if any remain
yearly_returns = yearly_returns.dropna(subset=["Yearly_Return"])

# Step 4: Average Return per Sector
sector_performance_df = (
    yearly_returns.groupby("Sector")["Yearly_Return"].mean().reset_index()
)



# VISUALISATION

plt.figure(figsize=(12,6))
plt.bar(sector_performance_df["Sector"], sector_performance_df["Yearly_Return"], color="orange")
plt.title("Average Yearly Return by Sector")
plt.xlabel("Sector")
plt.ylabel("Average Yearly Return")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# STOCK PRICE CORRELATION

yearly_returns = data.groupby("Ticker").apply(
    lambda x: (x["close"].iloc[-1] - x["close"].iloc[0]) / x["close"].iloc[0]
).reset_index(name="Yearly_Return")

top10_tickers = yearly_returns.sort_values("Yearly_Return", ascending=False).head(10)["Ticker"].tolist()

pivot_df = data[data["Ticker"].isin(top10_tickers)].pivot_table(
    index="date", columns="Ticker", values="close", aggfunc="mean"
)
returns = pivot_df.pct_change().dropna()

correlation_matrix_df = returns.corr()


# VISUALISATION

plt.figure(figsize=(10,8))
plt.imshow(correlation_matrix_df, cmap="coolwarm", interpolation="nearest")
plt.colorbar()
plt.xticks(range(len(correlation_matrix_df)), correlation_matrix_df.columns, rotation=90)
plt.yticks(range(len(correlation_matrix_df)), correlation_matrix_df.columns)
plt.title("Top 10 Stocks Price Correlation Heatmap")
plt.show()



# TOP 5 GAINERS AND LOSERS



monthly_returns = data.groupby(["Ticker", data["date"].dt.to_period("M")]).apply(
    lambda x: (x["close"].iloc[-1] - x["close"].iloc[0]) / x["close"].iloc[0]
).reset_index(name="Monthly_Return")

top_gainers = monthly_returns.groupby("date").apply(lambda x: x.nlargest(5, "Monthly_Return")).reset_index(drop=True)
top_losers = monthly_returns.groupby("date").apply(lambda x: x.nsmallest(5, "Monthly_Return")).reset_index(drop=True)


top_gainers["Type"] = "Gainer"
top_losers["Type"] = "Loser"
monthly_gainers_losers_df = pd.concat([top_gainers, top_losers])


# VISUALISATION



monthly_gainers_losers_df["date"] = monthly_gainers_losers_df["date"].astype(str)

months = sorted(monthly_gainers_losers_df["date"].unique())


fig, axes = plt.subplots(len(months), 2, figsize=(18, 48))
axes = axes.flatten()

for i, month in enumerate(months):
    
    month_data = monthly_gainers_losers_df[monthly_gainers_losers_df["date"] == month]
    

    gainers = month_data[month_data["Type"] == "Gainer"]
    losers = month_data[month_data["Type"] == "Loser"]
    axes[2*i].bar(gainers["Ticker"], gainers["Monthly_Return"], color="green")
    axes[2*i].set_title(f"{month} - Top 5 Gainers")
    axes[2*i].set_ylabel("Monthly Return")
    axes[2*i].tick_params(axis='x', rotation=45)
    for idx, val in enumerate(gainers["Monthly_Return"]):
        axes[2*i].text(idx, val, f"{val:.2%}", ha="center", va="bottom")
    

    axes[2*i+1].bar(losers["Ticker"], losers["Monthly_Return"], color="red")
    axes[2*i+1].set_title(f"{month} - Top 5 Losers")
    axes[2*i+1].set_ylabel("Monthly Return")
    axes[2*i+1].tick_params(axis='x', rotation=45)
    for idx, val in enumerate(losers["Monthly_Return"]):
        axes[2*i+1].text(idx, val, f"{val:.2%}", ha="center", va="bottom")

plt.tight_layout()
plt.show()


# PUSHING TO SQL

engine = create_engine("mysql+pymysql://root:123456@localhost:3306/stock_analysis")


volatility_df.to_sql("volatility_analysis", con=engine, if_exists="replace", index=False)


final_returns = data.groupby('Ticker')['cumulative_return'].last().sort_values(ascending=False)
cumulative_return_df = final_returns.head(5).reset_index()   # ✅ Now it's a DataFrame
cumulative_return_df.columns = ["Ticker", "Cumulative_Return"]

cumulative_return_df.to_sql("cumulative_return", con=engine, if_exists="replace", index=False)

sector_performance_df.to_sql("sector_performance", con=engine, if_exists="replace", index=False)


correlation_matrix_df_reset = correlation_matrix_df.reset_index()
correlation_matrix_df_reset.to_sql("stock_correlation", con=engine, if_exists="replace", index=False)


monthly_gainers_losers_df.to_sql("monthly_gainers_losers", con=engine, if_exists="replace", index=False)

# STREAMLIT APP

# STREAMLIT APP

st.title("📊 Stock Market Analysis Dashboard")

# ✅ Selection button right below the title
option = st.radio(
    "Choose a dataset or visualization:",
    (
        "All Stocks 📑",
        "Volatility 🔥",
        "Cumulative Return Over Time 📈💹📊",
        "Sector Performance 🏭📊",
        "Correlation Matrix 🔗📊",
        "Monthly Gainers/Losers 📅📈📉"
    )
)

# Show based on selection
if option == "All Stocks 📑":
    st.subheader("📑 Complete Stock Dataset")
    st.dataframe(data)

elif option == "Volatility 🔥":
    st.subheader("🔥 Top 10 Most Volatile Stocks")
    st.dataframe(volatility_df)
    fig, ax = plt.subplots(figsize=(10,6))
    ax.bar(volatility_df["Ticker"], volatility_df["Volatility"], color="orange")
    ax.set_title("Volatility of Top 10 Stocks")
    ax.set_xlabel("Ticker")
    ax.set_ylabel("Volatility")
    ax.tick_params(axis="x", rotation=45)
    st.pyplot(fig)

elif option == "Cumulative Return Over Time 📈💹📊":
    st.subheader("📈💹📊 Cumulative Return Over Time (Top 5 Stocks)")
    st.dataframe(cumulative_return_df)
    fig, ax = plt.subplots(figsize=(12,6))
    for ticker in cumulative_return_df["Ticker"]:
        subset = data[data["Ticker"] == ticker]
        ax.plot(subset["date"], subset["cumulative_return"], label=ticker, linewidth=2)
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=1)  # baseline
    ax.set_title("Cumulative Return Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative Return")
    ax.legend()
    plt.xticks(rotation=45)
    st.pyplot(fig)

elif option == "Sector Performance 🏭📊":
    st.subheader("🏭📊 Average Yearly Return by Sector")
    st.dataframe(sector_performance_df)
    fig, ax = plt.subplots(figsize=(12,6))
    ax.bar(sector_performance_df["Sector"], sector_performance_df["Yearly_Return"], color="blue")
    ax.set_title("Sector Performance")
    ax.set_xlabel("Sector")
    ax.set_ylabel("Yearly Return")
    ax.tick_params(axis="x", rotation=45)
    st.pyplot(fig)

elif option == "Correlation Matrix 🔗📊":
    st.subheader("🔗📊 Correlation Matrix of Top 10 Stocks")
    st.dataframe(correlation_matrix_df)
    fig, ax = plt.subplots(figsize=(10,8))
    cax = ax.matshow(correlation_matrix_df, cmap="coolwarm")
    fig.colorbar(cax)
    ax.set_xticks(range(len(correlation_matrix_df.columns)))
    ax.set_yticks(range(len(correlation_matrix_df.columns)))
    ax.set_xticklabels(correlation_matrix_df.columns, rotation=90)
    ax.set_yticklabels(correlation_matrix_df.columns)
    ax.set_title("Stock Price Correlation Heatmap")
    st.pyplot(fig)

elif option == "Monthly Gainers/Losers 📅📈📉":
    st.subheader("📅📈📉 Top 5 Gainers and Losers (Month-wise)")
    st.dataframe(monthly_gainers_losers_df)
    month = st.selectbox("Select Month", monthly_gainers_losers_df["date"].unique())
    month_data = monthly_gainers_losers_df[monthly_gainers_losers_df["date"] == month]

    fig, axes = plt.subplots(1, 2, figsize=(14,6))

    gainers = month_data[month_data["Type"] == "Gainer"]
    losers = month_data[month_data["Type"] == "Loser"]

    axes[0].bar(gainers["Ticker"], gainers["Monthly_Return"], color="green")
    axes[0].set_title(f"{month} - Top 5 Gainers")
    axes[0].set_ylabel("Monthly Return")
    axes[0].tick_params(axis="x", rotation=45)

    axes[1].bar(losers["Ticker"], losers["Monthly_Return"], color="red")
    axes[1].set_title(f"{month} - Top 5 Losers")
    axes[1].set_ylabel("Monthly Return")
    axes[1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    st.pyplot(fig)
