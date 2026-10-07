import pandas as pd
import streamlit as st

CONSUMPTION_FILE = "Electricity_consumption_2015-2025.csv"
PRICE_FILE = "Electricity_price_2015-2025.csv"

@st.cache_data
def load_data() -> pd.DataFrame:
    # consumption: "time,kWh,Temperature" (comma separated, ISO timestamps)
    # price: "timestamp;Price" (semicolon separated, "HH:MM DD/MM/YYYY", decimal comma, cents)
    consumption = pd.read_csv(CONSUMPTION_FILE)
    price = pd.read_csv(PRICE_FILE, sep=";", decimal=",")
    price = price.rename(columns={"timestamp": "time"})

    # Convert time columns of both frames to pandas datetime
    consumption["time"] = pd.to_datetime(consumption["time"])
    price["time"] = pd.to_datetime(price["time"])
    # Join the frames on time
    combine_table = pd.merge(consumption, price, on="time")
    # Clear row with no value
    combine_table = combine_table.dropna(subset=["Temperature", "Price"])
    # Calculate hourly bill (price is in cents -> euros: / 100)
    combine_table["hourly_bill_eur"] = combine_table["Price"] * combine_table["kWh"] / 100
    
    return combine_table

combine_table = load_data()

# Time range inputs
with st.sidebar:
    st.subheader("Date range")

    start_date = st.date_input(
        "Start",
        value=combine_table["time"].min().date(),
        format="DD/MM/YYYY"
    )

    end_date = st.date_input(
        "End",
        value=combine_table["time"].max().date(),
        format="DD/MM/YYYY"
    )
    
    # Grouped by SelectBox
    group_by = st.selectbox(label="Group data by",
                             options=["Daily", "Weekly", "Monthly"])

    chart_selection = st.selectbox(
        "Show chart",
        options=["All", "Consumption", "Price", "Bill", "Temperature"],
    )

# Filter data by time range
filtered_combine_table: pd.DataFrame = combine_table[
    (combine_table["time"].dt.date >= start_date) &
    (combine_table["time"].dt.date <= end_date)
]

# Grouped values (daily / weekly / monthly): consumption, bill, avg price, avg temperature
daily_data = (
    filtered_combine_table
    .groupby(pd.Grouper(key="time", freq="D"))
    .agg(
        consumption_kwh=("kWh", "sum"),
        bill_eur=("hourly_bill_eur", "sum"),
        avg_price_cents=("Price", "mean"),
        avg_temperature=("Temperature", "mean"),
    )
    .reset_index()
)

weekly_data = (
    filtered_combine_table
    .groupby(pd.Grouper(key="time", freq="W"))
    .agg(
        consumption_kwh=("kWh", "sum"),
        bill_eur=("hourly_bill_eur", "sum"),
        avg_price_cents=("Price", "mean"),
        avg_temperature=("Temperature", "mean"),
    )
    .reset_index()
    )
    
monthly_data = (
    filtered_combine_table
    .groupby(pd.Grouper(key="time", freq="ME"))
    .agg(
        consumption_kwh=("kWh", "sum"),
        bill_eur=("hourly_bill_eur", "sum"),
        avg_price_cents=("Price", "mean"),
        avg_temperature=("Temperature", "mean"),
    )
    .reset_index()
)

period_data_map = {
    "Daily": daily_data,
    "Weekly": weekly_data,
    "Monthly": monthly_data
}

active_table = period_data_map[group_by].round(1)

# Change title by chart type selection
title_by_chart = {
    "All": "Electricity Overview",
    "Consumption": f"{group_by} Electricity Consumption",
    "Price": f"{group_by} Electricity Price",
    "Bill": f"{group_by} Electricity Bill",
    "Temperature": f"{group_by} Average Temperature",
}
st.title(title_by_chart[chart_selection])

charts = {
    "Consumption": ("consumption_kwh", "Electricity consumption (kWh)"),
    "Price": ("avg_price_cents", "Electricity price(¢)"),
    "Bill": ("bill_eur", "Electricity bill (€)"),
    "Temperature": ("avg_temperature", "Temperature (°C)"),
}

charts_to_render = charts if chart_selection == "All" else {
    chart_selection: charts[chart_selection]
}

for column, y_label in charts_to_render.values():
    st.line_chart(
        data=active_table,
        x="time",
        y=column,
        x_label="Time",
        y_label=y_label,
    )
