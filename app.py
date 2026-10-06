import pandas as pd
import streamlit as st

CONSUMPTION_FILE = "Electricity_consumption_2015-2025.csv"
PRICE_FILE = "Electricity_price_2015-2025.csv"

st.title("Electricity consumption and bill")


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

filtered_combine_table: pd.DataFrame = combine_table[
    (combine_table["time"].dt.date >= start_date) &
    (combine_table["time"].dt.date <= end_date)
]
# Chart by consumption
st.line_chart(
   active_table,
   x="time",
   y="consumption_kwh",
   x_label="Time",
   y_label="Electricity consumption (kWh)"
)

# Chart by price
st.line_chart(
   active_table,
   x="time",
   y="avg_price_cents",
   x_label="Time",
   y_label="Electricity price(¢)"
)

# Chart by bill
st.line_chart(
   active_table,
   x="time",
   y="bill_eur",
   x_label="Time",
   y_label="Electricity bill (€)"
)

# Chart by temperature
st.line_chart(
   active_table,
   x="time",
   y="avg_temperature",
   x_label="Time",
   y_label="Temperature (°C)"
)
