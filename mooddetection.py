import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import pyrebase
import cv2
from deepface import DeepFace
import numpy as np
import time
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import base64  # Import the base64 module

# Firebase Configuration
firebaseConfig = {
    "apiKey": "AIzaSyBO3FAKTvDmntQoAp7NvsnLpX7QeKA2-lM",
    "authDomain": "icaps-431e2.firebaseapp.com",
    "projectId": "icaps-431e2",
    "databaseURL": "https://icaps-431e2-default-rtdb.firebaseio.com/",
    "storageBucket": "icaps-431e2.appspot.com",
    "messagingSenderId": "232758325218",
    "appId": "1:232758325218:web:7afab972cb1b865bfad3bb",
    "measurementId": "G-YB9XQSS949"
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

# Initialize Firebase Admin for Authentication
def initialize_firebase_admin():
    if not firebase_admin._apps:
        cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)

initialize_firebase_admin()

# User Registration
def register_user(email, password):
    try:
        user = auth.create_user_with_email_and_password(email, password)
        st.success("User created successfully")
        return user
    except Exception as e:
        st.error(f"Failed to create user: {e}")

# User Login
def login_user(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        st.success("User logged in successfully")
        return user
    except Exception as e:
        st.error(f"Invalid credentials: {e}")

# Save Emotion to Realtime Database
def save_emotion(user_id, emotion):
    try:
        timestamp = datetime.utcnow().isoformat()
        db.child("users").child(user_id).child("emotions").push({
            "emotion": emotion,
            "timestamp": timestamp
        })
        # st.success(f"Emotion '{emotion}' saved to database.")
    except Exception as e:
        st.error(f"Failed to save emotion: {e}")

# Video Feed
def show_video_feed(user_id):
    faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("Unable to open default webcam.")
        return

    frame_window = st.image([])

    while True:
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to grab frame")
            break

        try:
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            dominant_emotion = result[0]['dominant_emotion'] if 'dominant_emotion' in result[0] else "No face detected"
            save_emotion(user_id, dominant_emotion)
        except Exception as e:
            dominant_emotion = "No face detected"

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, 1.1, 4)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame,
                    dominant_emotion,
                    (50, 50),
                    font, 1,
                    (0, 0, 255),
                    2,
                    cv2.LINE_4)

        frame_window.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        time.sleep(0.05)

    cap.release()

# Fetch and Plot Emotion Statistics from Realtime Da# Fetch and Plot Emotion Statistics from Realtime Database
# Fetch and Plot Emotion Statistics from Realtime Database
def plot_emotion_statistics():
    try:
        initialize_firebase_admin()  # Ensure Firebase Admin is initialized

        users = db.child("users").get()
        user_emotion_data = {}

        if users.each() is not None:
            for user in users.each():
                user_id = user.key()
                
                # Correctly fetch the user's email using Firebase Admin SDK
                user_record = firebase_admin.auth.get_user(user_id)
                user_email = user_record.email
                 
                emotions = db.child("users").child(user_id).child("emotions").get()
                emotion_counts = {}

                if emotions.each() is not None:
                    for emotion in emotions.each():
                        emotion_data = emotion.val()
                        emotion_type = emotion_data.get("emotion")
                        if emotion_type and emotion_type != "No face detected":
                            emotion_counts[emotion_type] = emotion_counts.get(emotion_type, 0) + 1

                total_emotions = sum(emotion_counts.values())
                emotion_percentages = {k: (v / total_emotions) * 100 for k, v in emotion_counts.items()}
                user_emotion_data[user_email] = emotion_percentages

            if user_emotion_data:
                # Convert user emotion data to a DataFrame
                df = pd.DataFrame(user_emotion_data).T.fillna(0)
                df.index.name = 'user_email'

                # Add a label column based on conditions
                def get_label(row):
                    if row.get('sad', 0) > 20:
                        return 'often gloomy', 'blue'
                    elif row.get('fear', 0) > 20:
                        return 'often anxious', 'purple'
                    else:
                        return 'Normal', 'yellow'

                df['label'], df['color'] = zip(*df.apply(get_label, axis=1))

                # Style the DataFrame
                def apply_styles(val, color):
                    return f'color: {color};'

                styled_df = df.style.apply(lambda row: [apply_styles(row['label'], row['color']) for _ in row], axis=1)

                # Remove the color column from display
                # styled_df = styled_df.hide_columns(['color'])

                st.write("Emotion Percentage per User")
                st.dataframe(styled_df, use_container_width=True)

                # Selectbox for choosing which user's emotion distribution to display
                selected_user = st.selectbox("Select a user to view their emotion distribution", list(user_emotion_data.keys()))

                if selected_user:
                    percentages = user_emotion_data[selected_user]
                    labels = list(percentages.keys())
                    sizes = list(percentages.values())
                    fig, ax = plt.subplots()
                    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                    ax.axis('equal')
                    st.subheader(f"Emotion distribution for user {selected_user}")
                    st.pyplot(fig)
            else:
                st.write("No emotion data available.")
        else:
            st.write("No users found in the database.")
    except Exception as e:
        st.error(f"Failed to retrieve and plot emotions: {e}")



# Custom CSS for background image and rectangle container
def set_background(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
    }}
        .login-container {{
        background: #FFFFFF;
        box-shadow: 0px 4px 4px rgba(0, 0, 0, 0.25);
        border-radius: 60px;
        padding: 40px;
        width: 784px;
        margin: 56px auto;
        text-align: center;
    }}
    .input-container {{
        position: relative;
        width: 100%;
        max-width: 441px;
        margin: 20px auto;
    }}
    .input-container input {{
        border: none;
        border-bottom: 2px solid #D9D9D9;
        outline: none;
        width: 100%;
        padding: 10px;
        font-size: 32px;
        line-height: 39px;
        color: #D9D9D9;
    }}
    .input-container input:focus {{
        border-bottom: 2px solid #000;
    }}
    .login-button {{
        background: linear-gradient(90deg, #262DDD 0%, #DB00FF 100%);
        border-radius: 28px;
        width: 100%;
        height: 56px;
        margin: 40px auto;
        color: white;
        font-size: 23px;
        line-height: 23px;
        border: none;
        cursor: pointer;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

def get_base64_of_bin_file(png_file):
    with open(png_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Load custom CSS and background image
set_background("backgroundimage.png")

# Streamlit App



st.markdown(
    """
    <style>
    .header {
        font-family: "Montserrat";
        font-size:40px;
        color:#FFFFFF;
        text-align:center;
        font-weight: bold;
        padding: 5px;
    }
    .subheader {
        font-family: "Montserrat";
        font-size:30px;
        color:#FFFFFF;
        text-align:center;
        padding: 30px;
    }
    </style>
    """,
    unsafe_allow_html=True
)



# Display the uploaded image above the "Start Ventner" button
# uploaded_image = "updateprogress.png"
# st.image(uploaded_image, caption="Lessen Your Burnouts with Ventner!", use_column_width=True)



menu = ["Log in as a student", "Log in as an admin"]
choice = st.sidebar.selectbox("Choose your role", menu)

st.markdown('<div class="header">Welcome to Ventner!</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Ready to refresh your mind?</div>', unsafe_allow_html=True)
# st.subheader("Login Section")
email = st.text_input("University Email")
password = st.text_input("Password", type='password')
if choice == "Log in as a student":
    set_background("backgroundimage.png")
    # if st.markdown('<button class="login-button" onclick="document.getElementById(\'login_student\').click()">Login</button>', unsafe_allow_html=True):
    if st.button("Login", key="login_student"):
        user = login_user(email, password)
        if user:
            figma_url = "https://www.figma.com/proto/1wC0QCBtmcSqlk1Fqql9Ho/Untitled?node-id=4-5&t=z7QrFiL7HTJNWQOj-1"
            # Display the uploaded image above the "Start Ventner" button
            uploaded_image = "updateprogress.png"
            st.image(uploaded_image, caption="Lessen Your Burnouts with Ventner!", use_column_width=True)
            st.markdown(
                f'<a href="{figma_url}" target="_blank"><button class="login-button">Start Ventner</button></a>',
                unsafe_allow_html=True
            )
            show_video_feed(user['localId'])

elif choice == "Log in as an admin":
    set_background("backgroundimage2.png")
    # if st.markdown('<button class="login-button" onclick="document.getElementById(\'login_admin\').click()">Login</button>', unsafe_allow_html=True):
    if st.button("Login", key="login_admin"): 
        user = login_user(email, password)
        if user:
            plot_emotion_statistics()
