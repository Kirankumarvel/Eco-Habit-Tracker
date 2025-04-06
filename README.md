# 🗓 Eco-Habit Tracker

Track daily green habits like watering plants, reducing plastic use, etc. Built with Streamlit and SQLite for simple data tracking and visualization.

## 🚀 Features
- Track habits with one click
- View your history and progress
- Visualize your eco-habits in a bar chart

## 🛠 Requirements
Make sure you have the required packages installed:
```bash
pip install -r requirements.txt
```

## ▶️ How to Run
Run the application using Streamlit:
```bash
streamlit run tracker_app.py
```

## 📦 Folder Structure
```
eco-habit-tracker/
├── tracker_app.py
├── eco_habits.db (auto-created)
├── requirements.txt
└── README.md
```

## 📋 Tracker App Code
```python
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
    c.execute("INSERT INTO habits (habit, date) VALUES (?, ?)", (habit, date_str))
    conn.commit()
    st.success(f"Habit '{habit}' logged for today!")

# --- Show Habit History ---
st.subheader("📅 Your Habit History")
data = pd.read_sql("SELECT habit, date FROM habits ORDER BY date DESC", conn)
st.dataframe(data)

# --- Habit Frequency Chart ---
st.subheader("📊 Habit Frequency")
chart_data = data.groupby("habit").count().rename(columns={"date": "Count"})
st.bar_chart(chart_data)
```

## 🔌 Optional Integrations
- Link with a smartwatch (e.g., Fitbit/Apple shortcuts)
- Push notifications via mobile app (use `streamlit` + `twilio`/`pushover`)

---

Made to inspire small habits for a better Earth 🌍




