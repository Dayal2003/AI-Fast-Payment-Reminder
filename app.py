import streamlit as st
import pandas as pd
import pywhatkit
import google.generativeai as genai
from datetime import datetime
import time
from PIL import Image

# --- PAGE SETUP ---
st.set_page_config(page_title="Fast AI Payment Bot", layout="wide")
st.title("⚡ AI Fast Payment Reminder")

# --- SIDEBAR ---
st.sidebar.header("⚙️ Configuration")

# 1. API Key
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
if api_key:
    genai.configure(api_key=api_key)

st.sidebar.markdown("---")

# 2. PAYMENT DETAILS (UPI Link Feature)
st.sidebar.header("💰 Payment Settings")
upi_id = st.sidebar.text_input("Apna UPI ID dalein (Ex: 9876543210@ybl)")
merchant_name = st.sidebar.text_input("Apna/Dukan ka Naam (Ex: Rahul Fitness)")

# QR Code Option (Abhi bhi rakha hai agar chahiye ho toh)
qr_file = st.sidebar.file_uploader("QR Code (Optional - Slow)", type=['png', 'jpg', 'jpeg'])
qr_path = "my_qr_code.png"
use_qr = False
if qr_file is not None:
    image = Image.open(qr_file)
    image.save(qr_path)
    use_qr = True
    st.sidebar.success("QR Saved!")

st.sidebar.markdown("---")

# 3. ADD CLIENT
st.sidebar.header("➕ Add New Client")
new_name = st.sidebar.text_input("Naam")
new_phone = st.sidebar.text_input("Phone (+91..)")
new_date = st.sidebar.date_input("Due Date")

if st.sidebar.button("Save Client"):
    try:
        df = pd.read_excel('clients.xlsx')
    except:
        df = pd.DataFrame(columns=['Name', 'Phone', 'DueDate'])
    
    new_data = pd.DataFrame({'Name': [new_name], 'Phone': [new_phone], 'DueDate': [new_date.strftime("%d-%m-%Y")]})
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_excel('clients.xlsx', index=False)
    st.sidebar.success("Client Added!")

# --- MAIN DASHBOARD ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Pending Payments")
    try:
        df = pd.read_excel('clients.xlsx')
        st.dataframe(df, use_container_width=True)
    except:
        st.info("List khali hai.")

with col2:
    st.subheader("🚀 Send Reminders")
    tone = st.selectbox("Message Tone:", ["Professional", "Friendly", "Urgent", "Short"])
    
    if st.button("Generate & Send Now"):
        if not api_key:
            st.error("API Key missing!")
        elif not upi_id:
            st.error("UPI ID zaroori hai link banane ke liye!")
        else:
            today = datetime.now().strftime("%d-%m-%Y")
            model = genai.GenerativeModel('gemini-pro')
            st.write("Sending messages...")
            progress = st.progress(0)
            count = 0
            
            for index, row in df.iterrows():
                if row['DueDate'] == today:
                    name = row['Name']
                    phone = str(row['Phone'])
                    
                    # --- 1. AI Message ---
                    prompt = f"Write a polite payment reminder for {name}. Tone: {tone}. Max 15 words. No placeholders."
                    response = model.generate_content(prompt)
                    ai_msg = response.text
                    
                    # --- 2. MAGIC LINK CREATION ---
                    # Yeh format phone mein direct payment app kholta hai
                    # upi://pay?pa=UPI_ID&pn=NAME&cu=INR
                    # Note: Space ki jagah %20 use karein name mein
                    safe_name = merchant_name.replace(" ", "%20")
                    payment_link = f"upi://pay?pa={upi_id}&pn={safe_name}&cu=INR"
                    
                    final_msg = f"{ai_msg}\n\n👇 *Tap Link to Pay:*\n{payment_link}"
                    
                    st.info(f"Sending to {name}...")
                    
                    try:
                        # QR Code agar upload kiya hai toh wo use hoga, nahi toh Link (Fast)
                        if use_qr:
                            pywhatkit.sendwhats_image(phone, qr_path, final_msg, tab_close=True, wait_time=20)
                        else:
                            pywhatkit.sendwhatmsg_instantly(phone, final_msg, wait_time=15, tab_close=True)
                        
                        count += 1
                        time.sleep(6) 
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            progress.progress(100)
            if count > 0:
                st.success(f"Sent {count} reminders successfully!")
            else:
                st.warning("Aaj koi due date nahi hai.")