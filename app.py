import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import urllib.parse

# --- SETUP ---
st.set_page_config(page_title="Pro Payment Manager", layout="wide")
st.title("💼 AI Payment Manager (Pro Version)")

# --- AUTO-FIX EXCEL (Schema Migration) ---
# Agar purani file mein naye columns nahi hain, toh ye unhe add kar dega
try:
    df_check = pd.read_excel('clients.xlsx')
    required_columns = ['Name', 'Phone', 'DueDate', 'Advance', 'Offer', 'History']
    for col in required_columns:
        if col not in df_check.columns:
            df_check[col] = "" # Naye columns ko khali bana do
            if col == 'Advance':
                df_check[col] = 0 # Advance ko 0 set karo
    df_check.to_excel('clients.xlsx', index=False)
except:
    pass # Agar file nahi hai, toh neeche naya ban jayega

# --- SIDEBAR (Configuration) ---
st.sidebar.header("⚙️ Configuration")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
if api_key:
    genai.configure(api_key=api_key)

st.sidebar.markdown("---")
st.sidebar.header("💰 Merchant Details")
upi_id = st.sidebar.text_input("UPI ID (e.g. gym@upi)")
merchant_name = st.sidebar.text_input("Merchant Name")

# --- SIDEBAR (Add Client) ---
st.sidebar.markdown("---")
st.sidebar.header("➕ Add/Update Client")
new_name = st.sidebar.text_input("Name")
new_phone = st.sidebar.text_input("Phone (with +91)")
new_date = st.sidebar.date_input("Next Bill Due Date")
new_advance = st.sidebar.number_input("Advance Payment (₹)", min_value=0, value=0)
new_offer = st.sidebar.text_input("Special Offer (Optional)", placeholder="e.g. 10% Off on yearly plan")

if st.sidebar.button("Save Client Data"):
    try:
        df = pd.read_excel('clients.xlsx')
    except:
        df = pd.DataFrame(columns=['Name', 'Phone', 'DueDate', 'Advance', 'Offer', 'History'])
    
    clean_phone = str(new_phone).replace(" ", "").replace("-", "")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Check agar customer pehle se hai (Update Mode)
    if clean_phone in df['Phone'].astype(str).values:
        idx = df[df['Phone'].astype(str) == clean_phone].index[0]
        df.at[idx, 'Name'] = new_name
        df.at[idx, 'DueDate'] = new_date.strftime("%d-%m-%Y")
        df.at[idx, 'Advance'] = new_advance
        df.at[idx, 'Offer'] = new_offer
        # History mein aaj ki date update kar do
        current_history = str(df.at[idx, 'History']) if pd.notna(df.at[idx, 'History']) else ""
        df.at[idx, 'History'] = f"{current_history} | Updated on {today_str}"
        st.sidebar.success(f"Updated details for {new_name}!")
    else:
        # Naya Customer (Add Mode)
        new_data = pd.DataFrame({
            'Name': [new_name], 
            'Phone': [clean_phone], 
            'DueDate': [new_date.strftime("%d-%m-%Y")],
            'Advance': [new_advance],
            'Offer': [new_offer],
            'History': [f"Joined on {today_str}"]
        })
        df = pd.concat([df, new_data], ignore_index=True)
        st.sidebar.success("New Client Added!")
    
    df.to_excel('clients.xlsx', index=False)
    st.rerun()

# --- SIDEBAR (Delete Client) ---
st.sidebar.markdown("---")
with st.sidebar.expander("🗑️ Delete Client"):
    try:
        df_del = pd.read_excel('clients.xlsx')
        if not df_del.empty:
            name_to_delete = st.selectbox("Select Name", df_del['Name'].unique())
            if st.button("❌ Delete Permanently"):
                df_del = df_del[df_del['Name'] != name_to_delete]
                df_del.to_excel('clients.xlsx', index=False)
                st.rerun()
    except:
        pass

# --- MAIN APP ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Customer Register")
    try:
        df = pd.read_excel('clients.xlsx')
        if not df.empty:
            # Display only important columns
            st.dataframe(df[['Name', 'Phone', 'DueDate', 'Advance', 'Offer']], use_container_width=True)
            
            # Show History Expander
            with st.expander("📜 View Full History Logs"):
                st.dataframe(df[['Name', 'History']])
        else:
            st.info("No data found.")
    except:
        st.info("Start adding clients from the sidebar!")

with col2:
    st.subheader("🚀 Action Center")
    tone = st.selectbox("Tone:", ["Polite", "Strict", "Funny", "Professional"])
    
    if st.button("Generate Messages"):
        if not api_key:
            st.error("API Key missing!")
        else:
            model = genai.GenerativeModel('gemini-pro')
            st.write("---")
            
            try:
                df = pd.read_excel('clients.xlsx')
                for index, row in df.iterrows():
                    name = row['Name']
                    phone = str(row['Phone'])
                    advance = row['Advance']
                    offer = row['Offer']
                    due_date = row['DueDate']
                    
                    # --- SMART PROMPT ENGINEERING ---
                    # Hum AI ko saara data denge taaki wo smart message banaye
                    details = f"Advance Paid: ₹{advance}. Due Date: {due_date}. Special Offer: {offer}."
                    prompt = f"""
                    Write a WhatsApp payment reminder for {name}. 
                    Tone: {tone}. Max 25 words.
                    Context: {details}
                    If they have advance, mention it. If they have an offer, mention it nicely.
                    """
                    
                    try:
                        response = model.generate_content(prompt)
                        ai_msg = response.text
                    except:
                        ai_msg = f"Hello {name}, payment reminder. Due: {due_date}"

                    # Payment Link Logic
                    final_msg = ai_msg
                    if upi_id:
                        safe_name = urllib.parse.quote(merchant_name if merchant_name else "Merchant")
                        # Agar advance 0 hai toh normal link, varna note
                        pay_link = f"upi://pay?pa={upi_id}&pn={safe_name}&cu=INR"
                        final_msg += f"\n\n👇 Pay Balance Here:\n{pay_link}"
                    
                    # WhatsApp Link
                    encoded_msg = urllib.parse.quote(final_msg)
                    wa_link = f"https://wa.me/{phone}?text={encoded_msg}"
                    
                    # Display Card
                    st.success(f"👤 **{name}**")
                    if advance > 0:
                        st.caption(f"✅ Advance: ₹{advance} Jama hai")
                    if offer:
                        st.caption(f"🎉 Offer Active: {offer}")
                        
                    st.text_area("Message:", value=final_msg, height=120, key=f"msg_{index}")
                    st.link_button(f"🚀 Send to {name}", wa_link)
                    st.markdown("---")
            except Exception as e:
                st.error(f"Error: {e}")
