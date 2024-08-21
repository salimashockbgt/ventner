import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import pyrebase
import cv2
from deepface import DeepFace
import numpy as np
import time
from datetime import datetime
import matplotlib.pyplot as plt

# Firebase Configuration
firebaseConfig = {
    "apiKey": "AIzaSyAyxaj9faanqIea9toe-8LOm4LuyCdtO8Q",
    "authDomain": "adminicaps.firebaseapp.com",
    "databaseURL": "https://icaps-431e2.firebaseio.com",
    "projectId": "adminicaps",
    "storageBucket": "adminicaps.appspot.com",
    "messagingSenderId": "241234587113",
    "appId": "1:241234587113:web:15ee5412d7cad6a645af78",
    "measurementId": "G-N1WT24YETQ"
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

# Initialize Firebase Admin
def initialize_firebase_admin():
    if not firebase_admin._apps:
        cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)

initialize_firebase_admin()
firestore_db = firestore.client()

def plot_emotion_statistics():
    try:
        users_ref = firestore_db.collection("users")
        all_emotions = {}

        # Stream users collection
        users = users_ref.stream()
        user_count = 0
        for user in users:
            user_count += 1
            st.write(f"Processing user: {user.id}")  # Debug statement
            emotions_ref = users_ref.document(user.id).collection("emotions")
            emotions_count = 0
            for emotion_doc in emotions_ref.stream():
                emotions_count += 1
                emotion_data = emotion_doc.to_dict()
                st.write(f"Fetched emotion data: {emotion_data}")  # Debug statement
                emotion = emotion_data.get("emotion")
                if emotion and emotion != "No face detected":
                    all_emotions[emotion] = all_emotions.get(emotion, 0) + 1

            st.write(f"Total emotions fetched for user {user.id}: {emotions_count}")

        st.write(f"Total users processed: {user_count}")
        st.write(f"All emotions collected: {all_emotions}")  # Debug statement

        if all_emotions:
            labels = list(all_emotions.keys())
            sizes = list(all_emotions.values())
            fig, ax = plt.subplots()
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
            st.pyplot(fig)
        else:
            st.write("No emotion data available.")
    except Exception as e:
        st.error(f"Failed to retrieve and plot emotions: {e}")

st.title("Mood Tracker")
plot_emotion_statistics()