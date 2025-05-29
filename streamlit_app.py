import streamlit as st
import sqlite3
import os
import pandas as pd
from datetime import datetime

# ---------- SETUP ----------
DB_NAME = "audit_system.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id TEXT PRIMARY KEY,
            client_name TEXT,
            contact_email TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS audits (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT,
            filename TEXT,
            upload_date TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(client_id)
        )
    """)
    conn.commit()
    conn.close()

# ---------- CLIENTS ----------
def add_client(client_id, client_name, contact_email):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO clients (client_id, client_name, contact_email) VALUES (?, ?, ?)",
              (client_id, client_name, contact_email))
    conn.commit()
    conn.close()

def get_clients():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT client_id, client_name FROM clients")
    results = c.fetchall()
    conn.close()
    return results

# ---------- AUDITS ----------
def save_audit_file(client_id, file):
    filename = f"{client_id}_{file.name}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(file.read())

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO audits (client_id, filename, upload_date) VALUES (?, ?, ?)",
              (client_id, filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return filepath

# ---------- UI ----------
init_db()
st.title("🔍 Guided Audit Assistant")

if "step" not in st.session_state:
    st.session_state.step = 1

menu = st.sidebar.selectbox("Menu", ["Register Client", "Upload Audit File", "Start Guided Audit"])

if menu == "Register Client":
    st.subheader("Register New Client")
    client_id = st.text_input("Client ID")
    client_name = st.text_input("Client Name")
    contact_email = st.text_input("Contact Email")
    if st.button("Register"):
        if client_id and client_name:
            add_client(client_id, client_name, contact_email)
            st.success("Client registered successfully.")
        else:
            st.warning("Please provide Client ID and Name.")

elif menu == "Upload Audit File":
    st.subheader("Upload Audit File")
    clients = get_clients()
    if clients:
        options = [f"{cid} - {name}" for cid, name in clients]
        selected = st.selectbox("Select Client", options)
        client_id = selected.split(" - ")[0]
        file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
        if file and st.button("Upload"):
            path = save_audit_file(client_id, file)
            st.session_state.uploaded_path = path
            st.success("File uploaded.")
            st.session_state.client_id = client_id
            st.session_state.step = 2
    else:
        st.warning("Please register a client first.")

elif menu == "Start Guided Audit" and st.session_state.step >= 2:
    st.subheader("Guided Audit - Step by Step")

    try:
        df = pd.read_excel(st.session_state.uploaded_path, engine="openpyxl")
    except Exception as e:
        st.error(f"Could not read Excel file: {e}")
    else:
        st.write("Step 1: Review OFFICERS section")
        # For now just show first few rows as dummy
        st.dataframe(df.head())

        action = st.radio("What do you want to do with this section?", ["✅ Confirm", "⚠️ Flag Issue", "📝 Add Note"])
        if action == "📝 Add Note":
            note = st.text_area("Write your note here")

        if st.button("Next Step"):
            st.success("Proceeding to next section...")
            # Here we would update to the next audit section, e.g., ACCOUNTS
            # This part is expandable

else:
    st.info("Please register client and upload file to begin guided audit.")
