import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Vendor Spend Dashboard", layout="wide")
st.title("💼 Vendor Spend & Contract Risk Explorer")

st.markdown("""
This tool allows finance and procurement teams to explore vendor spend trends, identify contract inefficiencies, and benchmark performance. 
Upload your spend data (CSV format) with columns like `Vendor`, `Category`, `Invoice Date`, and `Amount` to begin.
""")

# --- Upload CSV ---
uploaded_file = st.file_uploader("📤 Upload Your Vendor Spend CSV", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, parse_dates=['Invoice Date'])

        required_cols = {"Vendor", "Category", "Invoice Date", "Amount"}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ Missing columns! Required: {', '.join(required_cols)}")
            st.stop()

        st.success("✅ File loaded successfully!")

        # Filters
        with st.sidebar:
            st.header("🔍 Filters")
            selected_vendor = st.multiselect("Vendor", df["Vendor"].unique(), default=df["Vendor"].unique())
            selected_category = st.multiselect("Category", df["Category"].unique(), default=df["Category"].unique())
            df = df[(df["Vendor"].isin(selected_vendor)) & (df["Category"].isin(selected_category))]

        # Spend Overview
        st.header("📊 Spend Overview")
        total_spend = df['Amount'].sum()
        monthly_spend = df.set_index('Invoice Date').resample('M')['Amount'].sum().reset_index()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Spend", f"${total_spend:,.2f}")

        with col2:
            avg_monthly = monthly_spend['Amount'].mean()
            st.metric("Avg Monthly Spend", f"${avg_monthly:,.2f}")

        # Trend Chart
        spend_chart = alt.Chart(monthly_spend).mark_line(point=True).encode(
            x=alt.X('Invoice Date:T', title='Month'),
            y=alt.Y('Amount:Q', title='Monthly Spend ($)'),
            tooltip=['Invoice Date', 'Amount']
        ).properties(height=400, title="📈 Monthly Spend Trend")

        st.altair_chart(spend_chart, use_container_width=True)

        # Breakdown Table
        st.subheader("📌 Spend Breakdown by Vendor & Category")
        pivot = df.groupby(['Vendor', 'Category'])['Amount'].sum().reset_index().sort_values(by="Amount", ascending=False)
        st.dataframe(pivot.style.format({"Amount": "${:,.2f}"}))

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
else:
    st.info("👈 Upload a CSV file to get started!")
