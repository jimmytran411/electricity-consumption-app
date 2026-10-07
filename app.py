import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from functools import partial
from plotly.subplots import make_subplots

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
        options=[
            "All",
            "Consumption & Temperature",
            "Consumption",
            "Price",
            "Bill",
            "Temperature",
        ],
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
    "Consumption & Temperature": f"{group_by} Consumption and Temperature",
    "Consumption": f"{group_by} Electricity Consumption",
    "Price": f"{group_by} Electricity Price",
    "Bill": f"{group_by} Electricity Bill",
    "Temperature": f"{group_by} Average Temperature",
}
st.title(title_by_chart[chart_selection])

def render_consumption_temperature(table: pd.DataFrame) -> None:
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Bar(
            x=table["time"],
            y=table["consumption_kwh"],
            name="Electricity consumption",
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=table["time"],
            y=table["avg_temperature"],
            name="Temperature",
            mode="lines",
        ),
        secondary_y=True,
    )
    figure.update_xaxes(title_text="Time")
    figure.update_yaxes(title_text="Electricity consumption (kWh)", secondary_y=False)
    figure.update_yaxes(title_text="Temperature (°C)", secondary_y=True)
    st.plotly_chart(figure, use_container_width=True)


def render_line_chart(
    table: pd.DataFrame, *, column: str, y_label: str
) -> None:
    st.line_chart(
        data=table,
        x="time",
        y=column,
        x_label="Time",
        y_label=y_label,
    )


chart_renderers = {
    "Consumption & Temperature": render_consumption_temperature,
    "Consumption": partial(
        render_line_chart,
        column="consumption_kwh",
        y_label="Electricity consumption (kWh)",
    ),
    "Price": partial(
        render_line_chart,
        column="avg_price_cents",
        y_label="Electricity price(¢)",
    ),
    "Bill": partial(
        render_line_chart,
        column="bill_eur",
        y_label="Electricity bill (€)",
    ),
    "Temperature": partial(
        render_line_chart,
        column="avg_temperature",
        y_label="Temperature (°C)",
    ),
}

chart_names_to_render = (
    ("Consumption & Temperature","Consumption", "Temperature", "Price", "Bill")
    if chart_selection == "All"
    else (chart_selection,)
)

def render_statistics(table: pd.DataFrame) -> None:
    st.markdown(f"**{start_date:%d/%m/%Y} - {end_date:%d/%m/%Y}**")
    if table.empty:
        st.info("No data in the selected range.")
        return

    total_kwh = table["kWh"].sum()
    total_bill = table["hourly_bill_eur"].sum()
    # Hourly price is the plain mean; paid price is weighted by consumption
    avg_hourly_price = table["Price"].mean()
    avg_paid_price = total_bill / total_kwh * 100 if total_kwh else 0.0
    days = table["time"].dt.date.nunique()
    peak = table.iloc[int(table["kWh"].to_numpy().argmax())]

    st.metric("Total consumption", f"{total_kwh:,.1f} kWh")
    st.metric("Total bill", f"{total_bill:,.2f} €")
    st.metric("Average hourly price", f"{avg_hourly_price:.2f} ¢/kWh")
    st.metric(
        "Average paid price",
        f"{avg_paid_price:.2f} ¢/kWh",
    )
    st.metric("Average daily consumption", f"{total_kwh / days:,.1f} kWh")
    st.metric("Average daily bill", f"{total_bill / days:,.2f} €")
    st.metric("Average temperature", f"{table['Temperature'].mean():.1f} °C")


for chart_name in chart_names_to_render:
    chart_renderers[chart_name](active_table)

with st.sidebar:
    with st.expander("Statistics", expanded=True):
        render_statistics(filtered_combine_table)
