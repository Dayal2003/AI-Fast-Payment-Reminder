import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import time
import urllib.parse  # Link banane ke liye

# --- SETUP ---
st.set_page_config(page_title="AI Payment Bot", layout="wide")
st.title("⚡ AI Fast Payment Reminder (Cloud Version)")

# --- SIDEBAR ---
st.sidebar.header("⚙️ Configuration")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)

st.sidebar.markdown("---")
st.sidebar.header("💰 Payment Details")
upi_id = st.sidebar.text_input("UPI ID (e.g. 9876543210@ybl)")
merchant_name = st.sidebar.text_input("Merchant Name (e.g. Rahul Gym)")

st.sidebar.markdown("---")
st.sidebar.header("➕ Add Client")
new_name = st.sidebar.text_input("Naam")
new_phone = st.sidebar.text_input("Phone (with +91)")
new_date = st.sidebar.date_input("Due Date")

if st.sidebar.button("Save Client"):
    try:
        df = pd.read_excel('clients.xlsx')
    except:
        df = pd.DataFrame(columns=['Name', 'Phone', 'DueDate'])
    
    # Phone number clean karna (spaces hatana)
    clean_phone = str(new_phone).replace(" ", "").replace("-", "")
    
    new_data = pd.DataFrame({'Name': [new_name], 'Phone': [clean_phone], 'DueDate': [new_date.strftime("%d-%m-%Y")]})
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_excel('clients.xlsx', index=False)
    st.sidebar.success("Client Added!")

# --- MAIN APP ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Pending Payments")
    try:
        df = pd.read_excel('clients.xlsx')
        st.dataframe(df, use_container_width=True)
    except:
        st.info("No data found.")

with col2:
    st.subheader("🚀 Action Center")
    tone = st.selectbox("Tone:", ["Polite", "Strict", "Funny", "Short"])
    
    if st.button("Generate Messages"):
        if not api_key:
            st.error("Pehle API Key daalo!")
        else:
            today = datetime.now().strftime("%d-%m-%Y")
            model = genai.GenerativeModel('gemini-pro')
            
            st.write("---")
            found = False
            
            for index, row in df.iterrows():
                if row['DueDate'] == today:
                    found = True
                    name = row['Name']
                    phone = str(row['Phone'])
                    
                    # 1. AI Message
                    prompt = f"Write a payment reminder for {name}. Tone: {tone}. Max 20 words. No placeholders."
                    try:
                        response = model.generate_content(prompt)
                        ai_msg = response.text
                    except:
                        ai_msg = f"Hello {name}, payment reminder."

                    # 2. Payment Link
                    final_msg = ai_msg
                    if upi_id:
                        safe_name = urllib.parse.quote(merchant_name if merchant_name else "Merchant")
                        pay_link = f"upi://pay?pa={upi_id}&pn={safe_name}&cu=INR"
                        final_msg += f"\n\n👇 Pay Here:\n{pay_link}"
                    
                    # 3. WhatsApp Link Banana (Encoding)
                    encoded_msg = urllib.parse.quote(final_msg)
                    wa_link = f"https://wa.me/{phone}?text={encoded_msg}"
                    
                    # 4. Display Card
                    with st.container():
                        st.info(f"👤 **{name}**")
                        st.text_area("Message Preview:", value=final_msg, height=100, key=f"txt_{index}")
                        
                        # Green Button jo WhatsApp kholega
                        st.link_button(f"🚀 Send on WhatsApp to {name}", wa_link)
                        st.markdown("---")
            
            if not found:
                st.warning("Aaj kisi ki payment due nahi hai.")
