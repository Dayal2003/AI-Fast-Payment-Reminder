import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import urllib.parse

# --- 1. PAGE CONFIGURATION (Isse tab ka naam aur icon badlega) ---
st.set_page_config(
    page_title="PaymentPro AI Dashboard",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (Ye hai asli magic jo app ko sundar banayega) ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Card Style Containers */
    .css-1r6slb0, .css-12w0qpk {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #e0e0e0;
    }
    
    /* Metrics (Numbers) styling */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #2E86C1;
        font-weight: bold;
    }
    
    /* Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        height: 3em;
        transition: all 0.3s ease;
    }
    
    /* Success Button (Green) */
    div[data-testid="stButton"] > button:first-child {
        background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
        color: white;
        border: none;
    }
    div[data-testid="stButton"] > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    /* Headers */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        color: #2c3e50;
    }
    </style>
""", unsafe_allow_html=True)

# --- AUTO-FIX EXCEL ---
try:
    df_check = pd.read_excel('clients.xlsx')
    required_columns = ['Name', 'Phone', 'DueDate', 'Advance', 'Offer', 'History']
    for col in required_columns:
        if col not in df_check.columns:
            df_check[col] = "" if col != 'Advance' else 0
    df_check.to_excel('clients.xlsx', index=False)
except:
    pass

# --- SIDEBAR (Modern Look) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
st.sidebar.title("PaymentPro")
st.sidebar.markdown("---")

api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password")
if api_key:
    genai.configure(api_key=api_key)

with st.sidebar.expander("⚙️ Merchant Settings"):
    upi_id = st.text_input("UPI ID", placeholder="example@oksbi")
    merchant_name = st.text_input("Business Name", placeholder="My Shop")

st.sidebar.markdown("### 👥 Client Management")
tab1, tab2 = st.sidebar.tabs(["Add New", "Edit/Delete"])

with tab1:
    with st.form("add_client_form"):
        new_name = st.text_input("Customer Name")
        new_phone = st.text_input("Phone Number")
        new_date = st.date_input("Next Due Date")
        col_a, col_b = st.columns(2)
        new_advance = col_a.number_input("Advance (₹)", min_value=0)
        new_offer = col_b.text_input("Offer Code")
        submit_add = st.form_submit_button("➕ Add Customer")
        
        if submit_add:
            try:
                df = pd.read_excel('clients.xlsx')
            except:
                df = pd.DataFrame(columns=['Name', 'Phone', 'DueDate', 'Advance', 'Offer', 'History'])
            
            clean_phone = str(new_phone).replace(" ", "").replace("-", "")
            new_data = pd.DataFrame({
                'Name': [new_name], 'Phone': [clean_phone], 'DueDate': [new_date.strftime("%d-%m-%Y")],
                'Advance': [new_advance], 'Offer': [new_offer], 'History': [f"Joined: {datetime.now().strftime('%Y-%m-%d')}"]
            })
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_excel('clients.xlsx', index=False)
            st.success("Added!")
            st.rerun()

with tab2:
    try:
        df_del = pd.read_excel('clients.xlsx')
        if not df_del.empty:
            client_to_manage = st.selectbox("Select Client", df_del['Name'].unique())
            if st.button("🗑️ Delete Selected"):
                df_del = df_del[df_del['Name'] != client_to_manage]
                df_del.to_excel('clients.xlsx', index=False)
                st.rerun()
    except:
        st.caption("No clients found.")

# --- MAIN DASHBOARD ---

# 1. TOP STATS ROW (DASHBOARD FEEL)
st.title("📊 Dashboard Overview")

try:
    df = pd.read_excel('clients.xlsx')
    total_clients = len(df)
    total_advance = df['Advance'].sum() if 'Advance' in df.columns else 0
    today_due = 0 # Placeholder logic
except:
    total_clients = 0
    total_advance = 0

m1, m2, m3 = st.columns(3)
m1.metric("👥 Total Customers", f"{total_clients}", "+1 this week")
m2.metric("💰 Advance Collected", f"₹{total_advance:,}", "Secure")
m3.metric("📅 Active Reminders", "Auto-Mode", "On")

st.markdown("---")

# 2. SPLIT LAYOUT
c1, c2 = st.columns([1.8, 1.2])

with c1:
    st.subheader("📋 Client Database")
    try:
        df = pd.read_excel('clients.xlsx')
        if not df.empty:
            # Modern Table with Column Configuration
            st.dataframe(
                df,
                column_config={
                    "Name": st.column_config.TextColumn("Customer", help="Client Name", width="medium"),
                    "Advance": st.column_config.ProgressColumn("Advance Paid", format="₹%f", min_value=0, max_value=5000),
                    "Phone": st.column_config.TextColumn("Contact"),
                    "DueDate": "Due Date"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("👋 Welcome! Add your first client from the sidebar.")
    except:
        st.error("Database not initialized.")

with c2:
    st.subheader("🚀 AI Action Center")
    
    # Card-like container
    with st.container():
        st.markdown('<div style="background-color:white; padding:15px; border-radius:10px;">', unsafe_allow_html=True)
        
        tone = st.select_slider("Select Tone", options=["Strict", "Professional", "Polite", "Funny"], value="Polite")
        
        if st.button("✨ Generate Smart Messages", use_container_width=True):
            if not api_key:
                st.error("Please enter API Key in sidebar.")
            else:
                model = genai.GenerativeModel('gemini-pro')
                
                # Processing Loop
                try:
                    df = pd.read_excel('clients.xlsx')
                    for index, row in df.iterrows():
                        name = row['Name']
                        phone = str(row['Phone'])
                        adv = row['Advance']
                        
                        # Prompt
                        prompt = f"Write a {tone} payment reminder for {name}. Mention advance of ₹{adv} if > 0. Max 20 words."
                        try:
                            res = model.generate_content(prompt)
                            msg = res.text
                        except:
                            msg = f"Hello {name}, payment reminder."
                        
                        # Links
                        final_msg = msg
                        if upi_id:
                            pay_url = f"upi://pay?pa={upi_id}&pn={merchant_name}&cu=INR"
                            final_msg += f"\n\nLink: {pay_url}"
                        
                        wa_url = f"https://wa.me/{phone}?text={urllib.parse.quote(final_msg)}"
                        
                        # Result Card
                        st.success(f"Message for **{name}**")
                        st.code(final_msg, language=None)
                        st.link_button(f"📤 Send via WhatsApp", wa_url, use_container_width=True)
                        st.markdown("---")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
