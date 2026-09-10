import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Financial & Savings Dashboard", layout="wide")

st.title("💰 Financial & Savings Dashboard")
st.markdown("Track your variable spending, month-to-month lifestyle shifts, energy bills, and $3,000 monthly savings goal securely.")

# Secure file uploader (Files uploaded here stay private in your active session)
uploaded_file = st.file_uploader("Upload your transaction CSV file to view your dashboard", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Basic data prep
    df['Time'] = pd.to_datetime(df['Time'], utc=True, errors='coerce')
    df = df.dropna(subset=['Time'])
    
    expenses = df[df['Total (AUD)'] < 0].copy()
    expenses['Absolute_Total'] = expenses['Total (AUD)'].abs()
    expenses['Month_Num'] = expenses['Time'].dt.month
    expenses['Month'] = expenses['Time'].dt.strftime('%b')

    # Categories
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

    def get_bucket(cat):
        if pd.isna(cat):
            return 'Other'
        if cat in essential_cats:
            return 'Essential'
        elif cat in lifestyle_cats:
            return 'Lifestyle'
        else:
            return 'Other'

    expenses['Bucket'] = expenses['Category'].apply(get_bucket)

    # Metrics Row
    total_spent = expenses['Absolute_Total'].sum()
    col_m1, col_m2 = st.columns(2)
    col_m1.metric(label="Total Variable Spend YTD", value=f"${total_spent:,.2f}")

    # --- SECTION 1: MONTH-TO-MONTH LIFESTYLE COMPARISON ---
    st.markdown("---")
    st.subheader("📊 Month-to-Month Lifestyle Spending Breakdown")
    st.markdown("Compare how your discretionary/lifestyle spending shifts month over month.")

    lifestyle_df = expenses[expenses['Bucket'] == 'Lifestyle']
    
    if not lifestyle_df.empty:
        # Group lifestyle by month and category
        lifestyle_pivot = lifestyle_df.pivot_table(
            index='Month', 
            columns='Category', 
            values='Absolute_Total', 
            aggfunc='sum'
        ).fillna(0)
        
        # Sort months correctly
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        lifestyle_pivot = lifestyle_pivot.reindex([m for m in month_order if m in lifestyle_pivot.index])

        st.bar_chart(lifestyle_pivot)
        
        # Monthly lifestyle total trend
        lifestyle_monthly_total = lifestyle_df.groupby('Month')['Absolute_Total'].sum().reindex(lifestyle_pivot.index)
        st.markdown("**Total Lifestyle Spend per Month:**")
        st.line_chart(lifestyle_monthly_total)
    else:
        st.info("No lifestyle transactions found in this dataset.")

    # --- SECTION 2: ENERGY BILLS TRACKER (Flow Power & Alinta) ---
    st.markdown("---")
    st.subheader("⚡ Energy Bills Tracker (Flow Power & Alinta Energy)")
    st.markdown("Monitor your energy bills month-by-month.")

    energy_df = expenses[expenses['Payee'].str.contains('Flow Power|Alinta', case=False, na=False)].copy()

    if not energy_df.empty:
        energy_monthly = energy_df.groupby(['Month', 'Payee'])['Absolute_Total'].sum().unstack().fillna(0)
        st.bar_chart(energy_monthly)
        
        st.dataframe(energy_df[['Time', 'Payee', 'Absolute_Total']].sort_values(by='Time', ascending=False))
    else:
        st.info("No Flow Power or Alinta Energy transactions found in this dataset.")

    # --- SECTION 3: GENERAL OVERVIEWS ---
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Essential vs Lifestyle Split")
        bucket_totals = expenses.groupby('Bucket')['Absolute_Total'].sum()
        fig, ax = plt.subplots()
        ax.pie(bucket_totals, labels=bucket_totals.index, autopct='%1.1f%%', startangle=140, colors=['#4c72b0', '#c44e52', '#ccb974'])
        st.pyplot(fig)

    with col2:
        st.subheader("Top Spending Categories YTD")
        top_cats = expenses.groupby('Category')['Absolute_Total'].sum().sort_values(ascending=False).head(8)
        st.bar_chart(top_cats)

else:
    st.info("🔒 Please upload your monthly transaction CSV file above to view your live dashboard. Your data remains private and is only processed for your active viewing session.")
