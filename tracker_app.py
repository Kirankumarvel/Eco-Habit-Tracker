import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os

# --- DB Setup ---
conn = sqlite3.connect('eco_habits.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit TEXT,
    date TEXT
)''')
c.execute('''CREATE TABLE IF NOT EXISTS custom_habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit TEXT
)''')
conn.commit()

# --- Page Config ---
st.set_page_config(page_title="Eco-Habit Tracker", page_icon="🌱", layout="wide")

st.title("🌱 Eco-Habit Tracker")
st.caption("Track your daily green habits to build a better planet.")

# --- Habit Options ---
default_habit_options = [
    "Watered Plants 🪴", "Reduced Plastic Use ♻️", "Recycled 📦",
    "Used Public Transport 🚌", "Saved Electricity 💡",
    "Composted Food Waste 🍂", "Used a Reusable Water Bottle 🚰",
    "Planted a Tree 🌳", "Picked Up Litter 🚮", "Used Renewable Energy Sources 🌞",
    "Donated to Environmental Causes 🌍", "Participated in a Cleanup Drive 🧹",
    "Educated Others About Sustainability 📚", "Used Eco-Friendly Products 🌿",
    "Avoided Single-Use Plastics 🚯"
]
custom_habits = [row[0] for row in c.execute("SELECT habit FROM custom_habits").fetchall()]
habit_options = default_habit_options + custom_habits

# --- Log a Habit ---
st.subheader("✅ Log an Eco-Habit")
habit = st.selectbox("What eco-habit did you complete today?", habit_options)
confirm = st.checkbox(f"I confirm I completed: {habit}")
if st.button("Add to Log"):
    if confirm:
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            c.execute("INSERT INTO habits (habit, date) VALUES (?, ?)", (habit, date_str))
            conn.commit()
            st.success(f"🎉 Logged: '{habit}' on {date_str}")
        except Exception as e:
            st.error(f"❌ Error logging habit: {e}")
    else:
        st.warning("☝️ Please confirm before logging.")

# --- Add Custom Habit ---
st.subheader("➕ Add Custom Habit")
new_habit = st.text_input("Enter your custom habit:")
if st.button("Add Custom Habit"):
    if new_habit.strip():
        try:
            c.execute("INSERT INTO custom_habits (habit) VALUES (?)", (new_habit.strip(),))
            conn.commit()
            st.success(f"✅ Added new habit: '{new_habit.strip()}'")
        except Exception as e:
            st.error(f"❌ Error adding custom habit: {e}")
    else:
        st.warning("☝️ Please enter a valid habit.")

# --- Habit History ---
st.subheader("📅 Habit Log History")
try:
    data = pd.read_sql("SELECT habit, date FROM habits ORDER BY date DESC", conn)
    st.dataframe(data, use_container_width=True)
except Exception as e:
    st.error(f"❌ Error fetching history: {e}")

# --- Streak Tracker ---
st.subheader("🔥 Streak Tracker")
try:
    streaks = {}
    data['date'] = pd.to_datetime(data['date'])
    for habit in habit_options:
        habit_data = data[data['habit'] == habit].copy()
        habit_data = habit_data.sort_values('date')
        streak = max_streak = 0
        prev_date = None
        for d in habit_data['date']:
            if prev_date is not None and (d - prev_date).days == 1:
                streak += 1
            else:
                streak = 1
            max_streak = max(max_streak, streak)
            prev_date = d
        if max_streak > 0:
            streaks[habit] = max_streak
    if streaks:
        st.json(streaks)
    else:
        st.info("No streak data yet. Start logging habits!")
except Exception as e:
    st.error(f"❌ Error calculating streaks: {e}")

# --- Leaderboard ---
st.subheader("🏆 Eco-Score Leaderboard")
try:
    data['points'] = 10  # 10 points per entry
    leaderboard = data.groupby('habit')['points'].sum().sort_values(ascending=False)
    st.bar_chart(leaderboard)
except Exception as e:
    st.error(f"❌ Error generating leaderboard: {e}")

# --- Line Chart: Progress Over Time ---
st.subheader("📈 Habits Over Time")
try:
    time_chart = data.groupby('date').size().reset_index(name='Count')
    fig = px.line(time_chart, x='date', y='Count', title='Habits Logged Over Time')
    st.plotly_chart(fig)
except Exception as e:
    st.error(f"❌ Error plotting chart: {e}")

# --- Download CSV ---
st.subheader("📥 Export Habit Log")
if not data.empty:
    csv = data.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "eco_habit_logs.csv", "text/csv")
else:
    st.info("No data available to export.")

# --- Reminder System (Simulated for Web) ---
st.subheader("⏰ Daily Habit Reminder")
st.info("⚠️ Real desktop notifications require local execution. Here, we simulate reminders.")
if st.button("Simulate Reminder"):
    st.success("🔔 Reminder: Don't forget to log your eco-habit today!")

# --- Admin Tools (optional) ---
with st.expander("🛠 Admin Tools (Danger Zone)"):
    if st.button("Clear All Logs"):
        c.execute("DELETE FROM habits")
        conn.commit()
        st.warning("🚨 All habit logs cleared!")

    if st.button("Clear Custom Habits"):
        c.execute("DELETE FROM custom_habits")
        conn.commit()
        st.warning("🚨 All custom habits removed!")

# --- DB Cleanup on Exit ---
@st.cache_resource
def get_connection():
    return conn
