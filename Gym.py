import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
import cv2
import mediapipe as mp
import os

st.set_page_config(page_title="Gym AI Ultimate", layout="wide")

# -------------------------------
# FILE SETUP
# -------------------------------
if not os.path.exists("users.csv"):
    pd.DataFrame(columns=["username","password"]).to_csv("users.csv", index=False)

if not os.path.exists("progress.csv"):
    pd.DataFrame(columns=["User","Date","Weight","Exercise","Reps","Weight_Lifted"]).to_csv("progress.csv", index=False)

# -------------------------------
# LOAD DATA
# -------------------------------
users = pd.read_csv("users.csv")
progress = pd.read_csv("progress.csv")

# -------------------------------
# SESSION
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = ""

# -------------------------------
# LOGIN SYSTEM
# -------------------------------
def login():
    st.title("🔐 Gym Login")

    choice = st.radio("Select", ["Login","Signup"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if choice == "Login":
        if st.button("Login"):
            if not users.empty and ((users["username"]==username)&(users["password"]==password)).any():
                st.session_state.logged_in = True
                st.session_state.user = username
                st.success("Login Successful")
            else:
                st.error("Invalid credentials")

    else:
        if st.button("Signup"):
            new = pd.DataFrame([[username,password]], columns=["username","password"])
            new.to_csv("users.csv", mode="a", header=False, index=False)
            st.success("Account created")

# -------------------------------
# LOCATION (STATIC)
# -------------------------------
def get_location():
    lat = 21.1458
    lon = 79.0882
    return lat, lon

# -------------------------------
# MAP
# -------------------------------
def gym_map():
    st.subheader("🌍 Nearby Gyms")

    gyms = pd.DataFrame({
        "Gym": ["Gold's Gym","Talwalkars","Anytime Fitness","Cult Fit"],
        "lat": [21.1458,21.1300,21.1600,21.1500],
        "lon": [79.0882,79.0800,79.0900,79.1000],
        "Rating": [4.5,4.2,4.6,4.7]
    })

    fig = px.scatter_mapbox(
        gyms,
        lat="lat",
        lon="lon",
        hover_name="Gym",
        size="Rating",
        color="Rating",
        zoom=12
    )

    fig.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# BMI + DIET
# -------------------------------
def bmi_diet():
    st.title("⚖️ BMI + Diet AI")

    h = st.number_input("Height (cm)",100,250)
    w = st.number_input("Weight (kg)",30,200)

    if st.button("Calculate"):
        bmi = w/((h/100)**2)
        st.metric("BMI", round(bmi,2))

        if bmi < 18.5:
            st.info("High calorie diet 🍚🥛")
        elif bmi < 25:
            st.success("Balanced diet 🥗")
        else:
            st.warning("Low calorie diet 🥗")

# -------------------------------
# CALORIES
# -------------------------------
def calories():
    st.title("🔥 Calories Calculator")

    w = st.number_input("Weight")
    st.metric("Calories Need", int(w*24))

# -------------------------------
# WORKOUT
# -------------------------------
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180:
        angle = 360 - angle
    return angle


def squat_ai():
    st.title("🤖 AI Squat Counter (MediaPipe 0.10.33 Optimized)")

    run = st.button("▶ Start Camera")

    if run:
        cap = cv2.VideoCapture(0)

        import mediapipe as mp
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils

        count = 0
        stage = None

        stframe = st.empty()

        # ✅ NEW STYLE (IMPORTANT)
        with mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as pose:

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    st.warning("Camera not accessible")
                    break

                # Convert to RGB
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False

                results = pose.process(image)

                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                try:
                    landmarks = results.pose_landmarks.landmark

                    hip = [landmarks[24].x, landmarks[24].y]
                    knee = [landmarks[26].x, landmarks[26].y]
                    ankle = [landmarks[28].x, landmarks[28].y]

                    angle = calculate_angle(hip, knee, ankle)

                    # ✅ Improved Logic
                    if angle > 165:
                        stage = "up"
                    if angle < 90 and stage == "up":
                        stage = "down"
                        count += 1

                    # Draw angle
                    cv2.putText(image, f'Angle: {int(angle)}',
                                tuple(np.multiply(knee, [640, 480]).astype(int)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)

                except:
                    pass

                # Draw pose
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )

                # Counter UI
                cv2.rectangle(image, (0, 0), (250, 80), (0, 0, 0), -1)
                cv2.putText(image, f'Reps: {count}', (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

                stframe.image(image, channels="BGR")

        cap.release()

# -------------------------------
# MAIN APP
# -------------------------------
if not st.session_state.logged_in:
    login()

else:
    st.sidebar.title(f"👋 {st.session_state.user}")

    page = st.sidebar.radio("Menu", [
        "Progress",
        "PR",
        "BMI",
        "Calories",
        "Workout",
        "Leaderboard",
        "Map",
        "AI Squat"
    ])

    # -------------------------------
    if page == "Progress":
        st.title("📈 Progress Tracker")

        with st.form("f"):
            d = st.date_input("Date")
            w = st.number_input("Weight")
            ex = st.text_input("Exercise")
            r = st.number_input("Reps")
            wl = st.number_input("Weight Lifted")

            if st.form_submit_button("Add"):
                new = pd.DataFrame([[st.session_state.user,d,w,ex,r,wl]],
                                   columns=progress.columns)
                new.to_csv("progress.csv", mode="a", header=False, index=False)
                st.success("Added")

    # -------------------------------
    elif page == "PR":
        st.title("🏆 PR Tracker")
        df = pd.read_csv("progress.csv")
        if not df.empty:
            st.dataframe(df.groupby("Exercise")["Weight_Lifted"].max())

    # -------------------------------
    elif page == "Leaderboard":
        st.title("🏆 Leaderboard")
        df = pd.read_csv("progress.csv")
        if not df.empty:
            lb = df.groupby("User")["Weight_Lifted"].max().reset_index()
            st.dataframe(lb.sort_values(by="Weight_Lifted", ascending=False))

    # -------------------------------
    elif page == "BMI":
        bmi_diet()

    elif page == "Calories":
        calories()

    elif page == "Workout":
        workout()

    elif page == "Map":
        gym_map()

    elif page == "AI Squat":
        squat_ai()
