import streamlit as st
import mysql.connector
import pandas as pd
from dotenv import load_dotenv
import os
import pytz

# Load environment variables from .env file
load_dotenv()

# Function to fetch data from MySQL
def fetch_data(expiry_date=None):
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        query = "SELECT * FROM max_pain_data"
        if expiry_date:
            query += " WHERE expiry_date = %s"
            df = pd.read_sql(query, connection, params=(expiry_date,))
        else:
            df = pd.read_sql(query, connection)
        connection.close()

        # Convert record_time from UTC to IST
        df['record_time'] = pd.to_datetime(df['record_time']).dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')

        return df
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
        return pd.DataFrame()

# Streamlit UI
st.title("Max Pain Data Viewer")

# Filter options
expiry_date = st.text_input("Enter Expiry Date (YYYY-MM-DD):")

# Fetch and display data
if st.button("Fetch Data"):
    data = fetch_data(expiry_date)
    st.write(data)

# Display all data
if st.button("Show All Data"):
    data = fetch_data()
    st.write(data)

