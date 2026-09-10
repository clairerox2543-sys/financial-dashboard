import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Financial & Savings Dashboard", layout="wide")

st.title("💰 Claire's Financial & Savings Dashboard")
st.markdown("Track your variable spending, essential vs. lifestyle splits, and $3,000 monthly savings goal.")

# File uploader for your monthly CSV
uploaded_file = st.file_uploader("Upload your transaction CSV file (e.g., Up or ME Bank export)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Basic data prep
    df['Time'] = pd.to_datetime(df['Time'], utc=True, errors='coerce')
    df = df.dropna(subset=['Time'])
    expenses = df[df['Total (AUD)'] < 0].copy()
    expenses['Absolute_Total'] = expenses['Total (AUD)'].abs()
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
    st.metric(label="Total Variable Spend YTD", value=f"${total_spent:,.2f}")

    # Charts Layout
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Monthly Variable Spending Trend")
        monthly_trend = expenses.groupby('Month')['Absolute_Total'].sum()
        st.line_chart(monthly_trend)

    with col2:
        st.subheader("Essential vs Lifestyle Split")
        bucket_totals = expenses.groupby('Bucket')['Absolute_Total'].sum()
        fig, ax = plt.subplots()
        ax.pie(bucket_totals, labels=bucket_totals.index, autopct='%1.1f%%', startangle=140, colors=['#4c72b0', '#c44e52', '#ccb974'])
        st.pyplot(fig)

    st.subheader("Top Spending Categories")
    top_cats = expenses.groupby('Category')['Absolute_Total'].sum().sort_values(ascending=False).head(10)
    st.bar_chart(top_cats)

else:
    st.info("👈 Please upload your transaction CSV file using the sidebar or uploader above to view your live dashboard.")

    