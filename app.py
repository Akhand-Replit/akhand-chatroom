import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import base64
import json
import time
from datetime import datetime

# Load Firebase credentials from Streamlit Secrets
firebase_base64 = st.secrets["FIREBASE_KEY"]

if firebase_base64:
    firebase_json = base64.b64decode(firebase_base64).decode("utf-8")
    firebase_dict = json.loads(firebase_json)

    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_dict)
        firebase_admin.initialize_app(cred)

    db = firestore.client()
else:
    st.error("⚠️ Firebase credentials are missing! Set them up in Streamlit Cloud Secrets.")

# Page settings
st.set_page_config(page_title="💬 Chatroom", layout="wide")

# Custom Modern Styling
st.markdown("""
    <style>
        body {
            background-color: #0d1117;
        }
        .chat-container {
            width: 100%;
            max-width: 700px;
            margin: auto;
            height: 85vh;
            background-color: #202C33;
            padding: 15px;
            border-radius: 10px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }
        .message-box {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }
        .avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background-color: #f47174;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
            color: white;
            margin-right: 10px;
        }
        .message {
            padding: 12px 15px;
            border-radius: 20px;
            max-width: 60%;
            font-size: 14px;
            word-wrap: break-word;
        }
        .sent {
            background-color: #005c4b;
            color: white;
            align-self: flex-end;
            text-align: right;
            border-bottom-right-radius: 5px;
        }
        .received {
            background-color: #3A3B3C;
            color: white;
            align-self: flex-start;
            text-align: left;
            border-bottom-left-radius: 5px;
        }
        .timestamp {
            font-size: 10px;
            color: #a1a1a1;
            margin-top: 4px;
            text-align: right;
        }
        .input-container {
            position: fixed;
            bottom: 10px;
            left: 50%;
            transform: translateX(-50%);
            width: 100%;
            max-width: 700px;
            display: flex;
            background-color: #1c1e21;
            padding: 10px;
            border-radius: 20px;
            align-items: center;
        }
        .input-box {
            flex-grow: 1;
            border: none;
            background-color: #2c2c2c;
            color: white;
            padding: 10px;
            border-radius: 20px;
            font-size: 14px;
            outline: none;
        }
        .send-button {
            background-color: #f47174;
            border: none;
            padding: 10px 15px;
            border-radius: 50%;
            cursor: pointer;
            color: white;
            font-size: 16px;
            margin-left: 10px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("💬 Modern Chatroom")

# Initialize session state
if "chatroom_id" not in st.session_state:
    st.session_state.chatroom_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "seen_messages" not in st.session_state:
    st.session_state.seen_messages = set()

if st.session_state.chatroom_id:
    chatroom_id = st.session_state.chatroom_id
    username = st.session_state.username

    st.subheader(f"Chatroom: {chatroom_id}")

    # Retrieve messages
    chatroom_ref = db.collection("chatrooms").document(chatroom_id).get()
    if chatroom_ref.exists:
        messages = chatroom_ref.to_dict().get("messages", [])

        # Prevent duplicate messages
        new_messages = [msg for msg in messages if msg["timestamp"] not in st.session_state.seen_messages]
        for msg in new_messages:
            st.session_state.seen_messages.add(msg["timestamp"])

        # Sort messages
        new_messages.sort(key=lambda x: x["timestamp"])

        # Display chat messages in frame
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in new_messages:
            formatted_time = datetime.fromtimestamp(msg["timestamp"]).strftime("%I:%M %p")
            msg_class = "sent" if msg['user'] == username else "received"
            avatar_letter = msg["user"][0].upper()  # First letter as avatar

            if msg_class == "received":
                st.markdown(f"""
                    <div class="message-box">
                        <div class="avatar">{avatar_letter}</div>
                        <div class="message {msg_class}">
                            <b>{msg['user']}</b><br>
                            {msg['message']}<br>
                            <span class="timestamp">{formatted_time}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="message-box" style="justify-content: flex-end;">
                        <div class="message {msg_class}">
                            {msg['message']}<br>
                            <span class="timestamp">{formatted_time}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # Fixed input field at the bottom
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    chat_input = st.text_input("", key="chat_input", label_visibility="collapsed", placeholder="What is up?", help="Type your message here")
    
    if st.button(">", key="send_button", help="Send Message"):
        if chat_input:
            msg = {
                "user": username,
                "message": chat_input,
                "timestamp": time.time()
            }
            db.collection("chatrooms").document(chatroom_id).update({
                "messages": firestore.ArrayUnion([msg])
            })
    
    st.markdown('</div>', unsafe_allow_html=True)

    st.rerun()  # Refresh messages automatically
