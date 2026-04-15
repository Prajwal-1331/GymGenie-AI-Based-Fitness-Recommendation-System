import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
import cv2
import mediapipe as mp
import pyrebase


st.set_page_config(page_title="Gym AI Pro Max", layout="wide")

# -------------------------------
# 🔥 FIREBASE CONFIG (PUT YOUR KEYS)
# -------------------------------
firebase_config = {
    "apiKey": "YOUR_API_KEY",
    "authDomain": "YOUR_PROJECT.firebaseapp.com",
    "projectId": "YOUR_PROJECT_ID",
    "storageBucket": "YOUR_PROJECT.appspot.com",
    "messagingSenderId": "XXXX",
    "appId": "XXXX",
    "databaseURL": ""
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()

# -------------------------------
# SESSION
# -------------------------------
if "user" not in st.session_state:
    st.session_state.user = None

# -------------------------------
# LOGIN SYSTEM (FIREBASE)
# -------------------------------
def login():
    st.title("🔐 Firebase Login")

    choice = st.radio("", ["Login", "Signup"])

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if choice == "Login":
        if st.button("Login"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.user = user
                st.success("Logged in")
            except:
                st.error("Login failed")

    else:
        if st.button("Signup"):
            try:
                auth.create_user_with_email_and_password(email, password)
                st.success("Account created")
            except:
                st.error("Signup failed")

# -------------------------------
# SAVE PROGRESS TO FIREBASE
# -------------------------------
def save_progress(data):
    db.child("progress").push(data, st.session_state.user["idToken"])

# -------------------------------
# GET LOCATION (REAL GPS)
# -------------------------------
def get_location():
    def get_location():
    # Default user location (Nagpur)
    return 21.1458, 79.0882
    if loc:
        return loc["coords"]["latitude"], loc["coords"]["longitude"]
    return None, None

# -------------------------------
# GOOGLE MAPS GYM LOCATOR
# -------------------------------
def map_feature():
    st.subheader("🌍 Nearby Gyms")

    lat, lon = get_location()

    gyms = pd.DataFrame({
        "Gym": ["Gold's Gym", "Talwalkars", "Anytime Fitness", "Cult Fit"],
        "lat": [21.1458, 21.1300, 21.1600, 21.1500],
        "lon": [79.0882, 79.0800, 79.0900, 79.1000],
        "Rating": [4.5, 4.2, 4.6, 4.7]
    })

    fig = px.scatter_mapbox(
        gyms,
        lat="lat",
        lon="lon",
        hover_name="Gym",
        size="Rating",
        color="Rating",
        zoom=12,
        height=500
    )

    fig.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig, use_container_width=True)

    st.success(f"Showing gyms near: {lat}, {lon}")

# -------------------------------
# SQUAT AI
# -------------------------------
def calculate_angle(a,b,c):
    a=np.array(a); b=np.array(b); c=np.array(c)
    radians=np.arctan2(c[1]-b[1],c[0]-b[0])-np.arctan2(a[1]-b[1],a[0]-b[0])
    angle=np.abs(radians*180/np.pi)
    if angle>180: angle=360-angle
    return angle

def squat_ai():
    st.subheader("🏋️ AI Squat Counter")

    if st.button("Start"):
        cap=cv2.VideoCapture(0)
        mp_pose=mp.solutions.pose
        pose=mp_pose.Pose()

        count=0; stage=None
        stframe=st.empty()

        while cap.isOpened():
            ret,frame=cap.read()
            if not ret: break

            img=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            res=pose.process(img)

            if res.pose_landmarks:
                lm=res.pose_landmarks.landmark
                hip=[lm[24].x,lm[24].y]
                knee=[lm[26].x,lm[26].y]
                ankle=[lm[28].x,lm[28].y]

                angle=calculate_angle(hip,knee,ankle)

                if angle>160: stage="up"
                if angle<90 and stage=="up":
                    stage="down"
                    count+=1

                cv2.putText(frame,f"Reps:{count}",(20,50),
                            cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2)

            stframe.image(frame, channels="BGR")

        cap.release()

# -------------------------------
# MAIN APP
# -------------------------------
if not st.session_state.user:
    login()
else:
    st.sidebar.title("Gym AI 🚀")

    page = st.sidebar.radio("Menu", [
        "Progress",
        "Map",
        "AI Squat"
    ])

    # -------------------------------
    if page == "Progress":
        st.title("📈 Progress")

        with st.form("form"):
            date = st.date_input("Date")
            weight = st.number_input("Weight")
            ex = st.text_input("Exercise")
            reps = st.number_input("Reps")
            wl = st.number_input("Weight Lifted")

            if st.form_submit_button("Save"):
                save_progress({
                    "date": str(date),
                    "weight": weight,
                    "exercise": ex,
                    "reps": reps,
                    "weight_lifted": wl
                })
                st.success("Saved to Firebase ✅")

    # -------------------------------
    elif page == "Map":
        map_feature()

    # -------------------------------
    elif page == "AI Squat":
        squat_ai()
