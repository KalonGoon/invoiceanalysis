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
        df = pd.read_csv(uploaded_file, low_memory=False)

        # Try to coerce key columns if formatting is messy
        df.columns = df.columns.str.strip()
        df = df.rename(columns=lambda x: x.strip().title())

        required_cols = {"Vendor", "Category", "Invoice Date", "Amount"}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ Missing columns! Required: {', '.join(required_cols)}")
            st.stop()

        # Try converting data types
        df['Invoice Date'] = pd.to_datetime(df['Invoice Date'], errors='coerce')
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df.dropna(subset=['Invoice Date', 'Amount'], inplace=True)

        st.success("✅ File loaded successfully!")

        # Filters
        with st.sidebar:
            st.header("🔍 Filters")
            selected_vendor = st.multiselect("Vendor", sorted(df["Vendor"].dropna().unique()), default=sorted(df["Vendor"].dropna().unique()))
            selected_category = st.multiselect("Category", sorted(df["Category"].dropna().unique()), default=sorted(df["Category"].dropna().unique()))
            date_range = st.slider("Invoice Date Range", min_value=df['Invoice Date'].min().date(), max_value=df['Invoice Date'].max().date(), value=(df['Invoice Date'].min().date(), df['Invoice Date'].max().date()))

            df = df[(df["Vendor"].isin(selected_vendor)) &
                    (df["Category"].isin(selected_category)) &
                    (df['Invoice Date'].dt.date >= date_range[0]) &
                    (df['Invoice Date'].dt.date <= date_range[1])]

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

        # Trend Chart with Smoothing Option
        st.subheader("📈 Monthly Spend Trend")
        show_trend = st.checkbox("Show Smoothed Trend Line", value=True)
        base = alt.Chart(monthly_spend).encode(
            x=alt.X('Invoice Date:T', title='Month')
        )

        line = base.mark_line(point=True, color="#1f77b4").encode(
            y=alt.Y('Amount:Q', title='Monthly Spend ($)'),
            tooltip=['Invoice Date', 'Amount']
        )

        chart = line

        if show_trend:
            trend = base.transform_loess('Invoice Date', 'Amount', bandwidth=0.5).mark_line(color='orange').encode(
                y='Amount:Q'
            )
            chart += trend

        st.altair_chart(chart.properties(height=400), use_container_width=True)

        # Breakdown Table
        st.subheader("📌 Spend Breakdown by Vendor & Category")
        pivot = df.groupby(['Vendor', 'Category'])['Amount'].sum().reset_index().sort_values(by="Amount", ascending=False)
        st.dataframe(pivot.style.format({"Amount": "${:,.2f}"}))

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
else:
    st.info("👈 Upload a CSV file to get started!")
