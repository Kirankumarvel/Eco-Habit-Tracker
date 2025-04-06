import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- DB Setup ---
conn = sqlite3.connect('eco_habits.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit TEXT,
    date TEXT
)''')
conn.commit()

# --- UI ---
st.title("🌱 Eco-Habit Tracker")
st.write("Track your daily green habits to build a better planet!")

# --- Habit Input ---
habit_options = ["Watered Plants", "Reduced Plastic Use", "Recycled", "Used Public Transport", "Saved Electricity"]
habit = st.selectbox("What eco-habit did you complete today?", habit_options)
if st.button("✅ Add to Log"):
    date_str = datetime.now().strftime("%Y-%m-%d")
    try:
        c.execute("INSERT INTO habits (habit, date) VALUES (?, ?)", (habit, date_str))
        conn.commit()
        st.success(f"Habit '{habit}' logged for today!")
    except Exception as e:
        st.error(f"Error logging habit: {e}")

# --- Show Habit History ---
st.subheader("📅 Your Habit History")
try:
    data = pd.read_sql("SELECT habit, date FROM habits ORDER BY date DESC", conn)
    st.dataframe(data)
except Exception as e:
    st.error(f"Error fetching habit history: {e}")

# --- Habit Frequency Chart ---
st.subheader("📊 Habit Frequency")
try:
    chart_data = data.groupby("habit").count().rename(columns={"date": "Count"})
    st.bar_chart(chart_data)
except Exception as e:
    st.error(f"Error generating chart: {e}")

# --- Close DB Connection on Streamlit Stop ---
def close_db_connection():
    conn.close()

st.on_event("shutdown", close_db_connection)
