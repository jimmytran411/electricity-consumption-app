# Electricity App

A Streamlit dashboard for exploring electricity consumption, prices, bills, and temperature from 2015 to 2025.

## Run locally

From the project directory, create and activate a virtual environment, install the dependencies, and start Streamlit:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate the environment with `.venv\Scripts\activate` instead of `source .venv/bin/activate`.

Streamlit will print a local URL (usually <http://localhost:8501>) to open in your browser. Keep the two CSV data files in the project directory; the app reads them from there.
