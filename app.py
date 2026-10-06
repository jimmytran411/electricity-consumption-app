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
