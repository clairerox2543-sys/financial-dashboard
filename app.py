import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Financial & Savings Dashboard", layout="wide")

st.title("💰 Financial & Savings Dashboard")
st.markdown("Track your variable spending, month-to-month lifestyle shifts, energy bills, and dynamic savings targets securely.")

# --- SIDEBAR: SAVINGS GOAL PLANNER ---
st.sidebar.header("🎯 Savings & Budget Planner")
target_savings = st.sidebar.slider(
    "Target Monthly Savings Goal ($)", 
    min_value=1000, 
    max_value=6000, 
    value=3000, 
    step=250,
    help="Adjust your monthly savings goal to see how your tailored variable budget adapts."
)

# Secure file uploader
uploaded_file = st.file_uploader("Upload your transaction CSV file (Up, ING, or Combined)", type=["csv"])

# Fallback to local combined file if available
if uploaded_file is None:
    try:
        uploaded_file = "combined_transactions.csv"
    except:
        pass

if uploaded_file is not None:
    # Read CSV (handles both Up format and Combined format)
    df = pd.read_csv(uploaded_file)
    
    # Standardize columns based on file type
    if 'Time' in df.columns:
        df['Date'] = pd.to_datetime(df['Time'], utc=True, errors='coerce').dt.tz_localize(None)
        df['Amount'] = df['Total (AUD)']
    elif 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce')
        if 'Debit' in df.columns and 'Credit' in df.columns:
            df['Amount'] = df['Debit'].fillna(0) * -1 + df['Credit'].fillna(0)
        elif 'Total (AUD)' in df.columns:
            df['Amount'] = df['Total (AUD)']

    df = df.dropna(subset=['Date'])
    
    # Separate Inflows and Outflows
    inflows = df[df['Amount'] > 0].copy()
    outflows = df[df['Amount'] < 0].copy()
    outflows['Absolute_Total'] = outflows['Amount'].abs()
    outflows['Month'] = outflows['Date'].dt.strftime('%b')
    outflows['Month_Num'] = outflows['Date'].dt.month

    # Categories & Buckets
    essential_cats = [
        'Groceries', 'Utilities', 'Internet', 'Public Transport', 'Fuel', 
        'Health & Medical', 'Pets', 'Mobile Phone', 'Tolls', 
        'Car Insurance, Rego & Maintenance', 'Maintenance & Improvements', 'Fitness & Wellbeing'
    ]
    lifestyle_cats = [
        'Restaurants & Cafes', 'Takeaway', 'Events & Gigs', 'Clothing & Accessories', 
        'Homeware & Appliances', 'Taxis & Share Cars', 'Apps, Games & Software', 
        'TV, Music & Streaming', 'Hair & Beauty', 'Pubs & Bars', 'Hobbies', 
        'Booze', 'Gifts & Charity', 'Technology', 'Holidays & Travel'
    ]

    def get_bucket(row):
        cat = row.get('Category', 'Other')
        desc = str(row.get('Description', '')).lower()
        
        # Fixed essential keywords (Mortgage, Body Corporate, Rates, Energy)
        if any(k in desc fork in ['mortgage', 'osko', 'deft', 'body corporate', 'rates', 'cbhs', 'flow power', 'alinta']):
            return 'Fixed Essential'
        
        if pd.isna(cat) or cat == 'Other':
            return 'Other'
        if cat in essential_cats:
            return 'Essential'
        elif cat in lifestyle_cats:
            return 'Lifestyle'
        else:
            return 'Other'

    outflows['Bucket'] = outflows.apply(get_bucket, axis=1)

    # Metrics & Budget Calculation
    total_spent = outflows['Absolute_Total'].sum()
    avg_monthly_income = inflows['Amount'].sum() / max(1, outflows['Date'].dt.to_period('M').nunique())
    
    fixed_costs = outflows[outflows['Bucket'] == 'Fixed Essential']['Absolute_Total'].sum() / max(1, outflows['Date'].dt.to_period('M').nunique())
    
    # Available variable budget after fixed costs and target savings
    available_variable_budget = max(0, avg_monthly_income - fixed_costs - target_savings)

    # Metrics Display
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric(label="Est. Monthly Income", value=f"${avg_monthly_income:,.0f}")
    col_m2.metric(label="Locked Fixed Costs (Mortgage/Bills)", value=f"${fixed_costs:,.0f}")
    col_m3.metric(label="Tailored Variable Budget", value=f"${available_variable_budget:,.0f}/mo", delta=f"Target Savings: ${target_savings:,}")

    # --- SECTION 1: TAILORED BUDGET BREAKDOWN BASED ON SAVINGS GOAL ---
    st.markdown("---")
    st.subheader(f"🎯 Tailored Budget for ${target_savings:,}/mo Savings Goal")
    st.markdown("Your fixed costs (mortgage, body corporate, energy bills) are locked. Here is how your remaining variable budget splits between essentials and lifestyle:")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("### 🛡️ Essential Variable Spend")
        actual_essential = outflows[outflows['Bucket'] == 'Essential']['Absolute_Total'].sum() / max(1, outflows['Date'].dt.to_period('M').nunique())
        st.metric(label="Average Monthly Essential Spend", value=f"${actual_essential:,.0f}")
        st.caption("Includes groceries, utilities, health, transport, and fitness.")

    with col_b2:
        st.markdown("### 🎉 Lifestyle / Discretionary Spend")
        target_lifestyle = max(0, available_variable_budget - actual_essential)
        actual_lifestyle = outflows[outflows['Bucket'] == 'Lifestyle']['Absolute_Total'].sum() / max(1, outflows['Date'].dt.to_period('M').nunique())
        st.metric(label="Target Lifestyle Budget", value=f"${target_lifestyle:,.0f}", delta=f"Actual Avg: ${actual_lifestyle:,.0f}")
        st.caption("Dining out, entertainment, shopping, and hobbies adjusted to hit your savings target.")

    # --- SECTION 2: MONTH-TO-MONTH LIFESTYLE COMPARISON ---
    st.markdown("---")
    st.subheader("📊 Month-to-Month Lifestyle Spending Breakdown")
    lifestyle_df = outflows[outflows['Bucket'] == 'Lifestyle']
    
    if not lifestyle_df.empty:
        lifestyle_pivot = lifestyle_df.pivot_table(
            index='Month', 
            columns='Category', 
            values='Absolute_Total', 
            aggfunc='sum'
        ).fillna(0)
        
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        lifestyle_pivot = lifestyle_pivot.reindex([m for m in month_order if m in lifestyle_pivot.index])

        st.bar_chart(lifestyle_pivot)
    else:
        st.info("No lifestyle transactions found.")

    # --- SECTION 3: ENERGY BILLS TRACKER (Flow Power & Alinta) ---
    st.markdown("---")
    st.subheader("⚡ Energy Bills Tracker (Flow Power & Alinta Energy)")
    energy_df = outflows[outflows['Description'].str.contains('Flow Power|Alinta', case=False, na=False)].copy()

    if not energy_df.empty:
        energy_monthly = energy_df.groupby(['Month', 'Description'])['Absolute_Total'].sum().unstack().fillna(0)
        st.bar_chart(energy_monthly)
    else:
        st.info("No energy bill transactions detected.")

else:
    st.info("🔒 Please upload your combined transaction CSV file or ensure `combined_transactions.csv` is in your folder.")
