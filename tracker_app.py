# Run this in your Streamlit app environment

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF
import re

# --- Helper Functions --
def remove_emojis(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)

# --- DB Setup ---
conn = sqlite3.connect('eco_habits.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)''')
c.execute('''CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit TEXT,
    date TEXT
)''')

# Ensure the user_id column exists in the habits table
try:
    c.execute("ALTER TABLE habits ADD COLUMN user_id INTEGER")
except sqlite3.OperationalError:
    pass  # Column already exists
c.execute('''CREATE TABLE IF NOT EXISTS custom_habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    habit TEXT
)''')
# Ensure the custom_habits table exists
c.execute('''
    CREATE TABLE IF NOT EXISTS custom_habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        habit TEXT
    )
''')

# Ensure the user_id column exists in the custom_habits table
try:
    c.execute("ALTER TABLE custom_habits ADD COLUMN user_id INTEGER")
except sqlite3.OperationalError:
    pass  # Column already exists
conn.commit()

# --- Page Config ---
st.set_page_config(page_title="Eco-Habit Tracker", page_icon="🌱", layout="wide")
st.title("🌱 Eco-Habit Tracker")

# --- Session State for Login ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = ""

# --- Sidebar Auth ---
with st.sidebar:
    st.title("Login / Register")
    action = st.radio("Choose an action", ["Login", "Register"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button(action):
        if action == "Login":
            user = c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password)).fetchone()
            if user:
                st.session_state.user_id = user[0]
                st.session_state.username = username
                st.success(f"Welcome {username}!")
            else:
                st.error("Invalid credentials.")
        else:  # Register
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                user = c.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
                st.session_state.user_id = user[0]
                st.session_state.username = username
                st.success("Registered successfully! You are now logged in.")
            except sqlite3.IntegrityError:
                st.error("Username already exists.")

# --- Stop if not logged in ---
if not st.session_state.user_id:
    st.warning("Please log in to access the tracker.")
    st.stop()

user_id = st.session_state.user_id

# --- Habit Options ---
default_habit_options = [
    "Watered Plants 🪴", "Reduced Plastic Use ♻️", "Recycled 📦", "Used Public Transport 🚌",
    "Saved Electricity 💡", "Composted Food Waste 🍂", "Used a Reusable Water Bottle 🚰",
    "Planted a Tree 🌳", "Picked Up Litter 🚮", "Used Renewable Energy Sources 🌞",
    "Donated to Environmental Causes 🌍", "Participated in a Cleanup Drive 🧹",
    "Educated Others About Sustainability 📚", "Used Eco-Friendly Products 🌿",
    "Avoided Single-Use Plastics 🚯"
]
custom_habits = [row[0] for row in c.execute("SELECT habit FROM custom_habits WHERE user_id = ?", (user_id,)).fetchall()]
habit_options = default_habit_options + custom_habits

# --- Log Habit ---
st.subheader("✅ Log an Eco-Habit")
habit = st.selectbox("What eco-habit did you complete today?", habit_options)
confirm = st.checkbox(f"I confirm I completed: {habit}")
if st.button("Add to Log"):
    if confirm:
        date_str = datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO habits (user_id, habit, date) VALUES (?, ?, ?)", (user_id, habit, date_str))
        conn.commit()
        st.success(f"Logged: {habit} on {date_str}")
    else:
        st.warning("Please confirm before logging.")

# --- Add Custom Habit ---
st.subheader("➕ Add Custom Habit")
new_habit = st.text_input("Enter your custom habit:")
if st.button("Add Custom Habit"):
    if new_habit.strip():
        c.execute("INSERT INTO custom_habits (user_id, habit) VALUES (?, ?)", (user_id, new_habit.strip()))
        conn.commit()
        st.success(f"Added new habit: {new_habit.strip()}")
    else:
        st.warning("Please enter a valid habit.")

# --- Challenges ---
st.subheader("🎯 Daily/Weekly Challenges")
if st.button("Generate Challenge"):
    challenge = random.choice(default_habit_options)
    st.info(f"Your Eco Challenge: {challenge}")

# --- Gamification: Streaks & Badges ---
st.subheader("🏅 Streaks & Badges")

try:
    # Fetch user habits data
    habit_data = pd.read_sql("SELECT habit, date FROM habits WHERE user_id = ?", conn, params=(user_id,))
    habit_data['date'] = pd.to_datetime(habit_data['date'])

    # Calculate streaks for each habit
    streaks = {}
    for habit in habit_data['habit'].unique():
        habit_dates = habit_data[habit_data['habit'] == habit].sort_values("date")['date']
        streak = max_streak = 0
        previous_date = None

        for current_date in habit_dates:
            if previous_date and (current_date - previous_date).days == 1:
                streak += 1
            else:
                streak = 1
            max_streak = max(max_streak, streak)
            previous_date = current_date

        streaks[habit] = max_streak

    # Display streaks in a user-friendly format
    st.write("🌟 Your Habit Streaks:")
    for habit, max_streak in streaks.items():
        st.write(f"- **{habit}**: {max_streak} day(s)")

except Exception as e:
    st.error(f"An error occurred while calculating streaks: {e}")

# # --- Email Reminder ---
# st.subheader("📧 Send Email Reminder")
# email = st.text_input("Your Email Address")
# if st.button("Send Reminder Email"):
#     try:
#         sender_email = "your_email@gmail.com"
#         sender_pass = "your_password"  # Suggest using st.secrets for real usage
#         subject = "Eco-Habit Reminder"
#         body = "Hi there! Just a reminder to log your eco-friendly habit today. 🌱"
#         msg = MIMEMultipart()
#         msg['From'] = sender_email
#         msg['To'] = email
#         msg['Subject'] = subject
#         msg.attach(MIMEText(body, 'plain'))
#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
#         server.login(sender_email, sender_pass)
#         server.sendmail(sender_email, email, msg.as_string())
#         server.quit()
#         st.success("Reminder sent successfully!")
#     except Exception as e:
#         st.error(f"Error sending email: {e}")



# --- Monthly Summary Report ---
st.subheader("📊 Monthly Summary Report")
if st.button("Generate Report"):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16)
        pdf.set_text_color(34, 139, 34)  # Green color for the title
        pdf.cell(200, 10, txt="Monthly Eco-Habit Summary", ln=True, align='C')
        pdf.ln(10)  # Add some vertical space

        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0, 0, 0)  # Black color for the content

        report_data = pd.read_sql("SELECT habit, date FROM habits WHERE user_id = ? ORDER BY date DESC", conn, params=(user_id,))
        if not report_data.empty:
            pdf.set_fill_color(220, 220, 220)  # Light gray background for headers
            pdf.cell(90, 10, "Date", border=1, ln=0, align='C', fill=True)
            pdf.cell(100, 10, "Habit", border=1, ln=1, align='C', fill=True)

            for _, row in report_data.iterrows():
                clean_date = row['date']
                clean_habit = remove_emojis(row['habit'])
                pdf.cell(90, 10, clean_date, border=1, ln=0, align='C')
                pdf.cell(100, 10, clean_habit, border=1, ln=1, align='C')
        else:
            pdf.cell(200, 10, txt="No habits logged this month.", ln=True, align='C')

        report_path = f"monthly_summary_{st.session_state.username}.pdf"
        pdf.output(report_path)

        with open(report_path, "rb") as file:
            btn = st.download_button(
                label="Download Monthly Summary",
                data=file,
                file_name=report_path,
                mime="application/pdf"
            )
        st.success("Report generated successfully!")
    except Exception as e:
        st.error(f"Error generating report: {e}")

# --- Leaderboard ---
st.subheader("🏆 Eco-Score Leaderboard🏆")
try:
    # 🏆 Calculate scores for each user and display leaderboard
    leaderboard_query = """
        SELECT u.username, COUNT(h.id) AS score
        FROM users u
        LEFT JOIN habits h ON u.id = h.user_id
        GROUP BY u.id
        ORDER BY score DESC
        LIMIT 10
    """
    leaderboard_data = pd.read_sql(leaderboard_query, conn)
    if not leaderboard_data.empty and 'username' in leaderboard_data.columns and 'score' in leaderboard_data.columns:
        leaderboard_data.index += 1  # Rank starts from 1
        st.subheader("🏆 Eco-Score Leaderboard Table🌟")
        st.table(leaderboard_data)

        # --- Bar Chart for Leaderboard ---
        st.subheader("📊 Leaderboard Bar Chart")
        leaderboard_data['points'] = 10  # 10 points per entry
        leaderboard = leaderboard_data.groupby('username')['score'].sum().sort_values(ascending=False)
        st.bar_chart(leaderboard)
    else:
        st.warning("No data available for the leaderboard or missing required columns.")
except Exception as e:
    st.error(f"❌ Error generating leaderboard: {e}")
