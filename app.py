import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Amazon Sales Data Analysis",
    page_icon="📊",
    layout="wide"
)

# Function to load and preprocess data
@st.cache_data
def load_data():
    # Load the data
    df = pd.read_csv("Amazon Sales data.csv")
    
    # Convert date columns to datetime with mixed format
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='mixed', dayfirst=False)
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], format='mixed', dayfirst=False)
    
    # Extract year and month from Order Date
    df['Order Year'] = df['Order Date'].dt.year
    df['Order Month'] = df['Order Date'].dt.month
    
    # Calculate delivery time (days between order and shipping)
    df['Delivery Time'] = (df['Ship Date'] - df['Order Date']).dt.days
    
    # Calculate profit margin percentage
    df['Profit Margin %'] = (df['Total Profit'] / df['Total Revenue']) * 100
    
    return df

# Load the data
df = load_data()

# App title and description
st.title("📊 Amazon Sales Data Analysis Dashboard")
st.markdown("""
This dashboard provides insights into Amazon sales data, allowing you to explore sales trends,
regional performance, product categories, and profitability metrics.
""")

# Display raw data if requested
with st.expander("Show Raw Data"):
    st.dataframe(df)
    
    # Download button for the dataset
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download CSV",
        csv,
        "amazon_sales_data.csv",
        "text/csv",
        key='download-csv'
    )

# Create sidebar filters
st.sidebar.header("Filters")

# Select regions
regions = st.sidebar.multiselect(
    "Select Regions",
    options=sorted(df["Region"].unique()),
    default=sorted(df["Region"].unique())
)

# Select item types
item_types = st.sidebar.multiselect(
    "Select Item Types",
    options=sorted(df["Item Type"].unique()),
    default=sorted(df["Item Type"].unique())
)

# Select sales channels
sales_channels = st.sidebar.multiselect(
    "Select Sales Channels",
    options=sorted(df["Sales Channel"].unique()),
    default=sorted(df["Sales Channel"].unique())
)

# Date range filter
min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()
date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Apply filters
filtered_df = df[
    (df["Region"].isin(regions)) &
    (df["Item Type"].isin(item_types)) &
    (df["Sales Channel"].isin(sales_channels)) &
    (df["Order Date"].dt.date >= date_range[0]) &
    (df["Order Date"].dt.date <= date_range[1])
]

# KPI metrics in a row
st.header("Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Revenue", f"${filtered_df['Total Revenue'].sum():,.2f}")

with col2:
    st.metric("Total Profit", f"${filtered_df['Total Profit'].sum():,.2f}")

with col3:
    avg_margin = filtered_df['Profit Margin %'].mean()
    st.metric("Average Profit Margin", f"{avg_margin:.2f}%")

with col4:
    st.metric("Total Units Sold", f"{filtered_df['Units Sold'].sum():,}")

# Sales analysis by region
st.header("Regional Sales Analysis")
region_tab1, region_tab2 = st.tabs(["Revenue by Region", "Profit by Region"])

with region_tab1:
    # Create a regional revenue analysis
    region_revenue = filtered_df.groupby("Region")["Total Revenue"].sum().reset_index()
    fig = px.bar(
        region_revenue,
        x="Region",
        y="Total Revenue",
        title="Total Revenue by Region",
        color="Region",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

with region_tab2:
    # Create a regional profit analysis
    region_profit = filtered_df.groupby("Region")["Total Profit"].sum().reset_index()
    fig = px.bar(
        region_profit,
        x="Region",
        y="Total Profit",
        title="Total Profit by Region",
        color="Region",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

# Product analysis
st.header("Product Analysis")
product_tab1, product_tab2 = st.tabs(["Revenue by Product", "Profit Margin by Product"])

with product_tab1:
    # Revenue by item type
    item_revenue = filtered_df.groupby("Item Type")["Total Revenue"].sum().sort_values(ascending=False).reset_index()
    fig = px.pie(
        item_revenue,
        values="Total Revenue",
        names="Item Type",
        title="Revenue Distribution by Product Type",
        hole=0.4,
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

with product_tab2:
    # Profit margin by item type
    item_margin = filtered_df.groupby("Item Type")[["Total Revenue", "Total Profit"]].sum().reset_index()
    item_margin["Margin %"] = (item_margin["Total Profit"] / item_margin["Total Revenue"] * 100).round(2)
    item_margin = item_margin.sort_values("Margin %", ascending=False)
    
    fig = px.bar(
        item_margin,
        x="Item Type",
        y="Margin %",
        title="Profit Margin % by Product Type",
        color="Item Type",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

# Time series analysis
st.header("Sales Trends Over Time")
time_tab1, time_tab2 = st.tabs(["Monthly Trends", "Sales Channel Performance"])

with time_tab1:
    # Monthly sales and profit trends
    monthly_data = filtered_df.groupby(["Order Year", "Order Month"])[["Total Revenue", "Total Profit"]].sum().reset_index()
    
    # Construct date strings explicitly
    monthly_data["Date"] = pd.to_datetime(monthly_data.apply(lambda row: f"{int(row['Order Year'])}-{int(row['Order Month']):02}-01", axis=1))
    
    monthly_data = monthly_data.sort_values("Date")
    
    fig = px.line(
        monthly_data,
        x="Date",
        y=["Total Revenue", "Total Profit"],
        title="Monthly Sales and Profit Trends",
        template="plotly_white",
        labels={"value": "Amount ($)", "variable": "Metric"}
    )
    st.plotly_chart(fig, use_container_width=True)

with time_tab2:
    # Sales channel performance over time
    channel_data = filtered_df.groupby(["Order Year", "Order Month", "Sales Channel"])[["Total Revenue"]].sum().reset_index()
    channel_data["Date"] = pd.to_datetime(channel_data.apply(lambda row: f"{int(row['Order Year'])}-{int(row['Order Month']):02}-01", axis=1))    
    channel_data = channel_data.sort_values("Date")
    
    fig = px.line(
        channel_data,
        x="Date",
        y="Total Revenue",
        color="Sales Channel",
        title="Sales Channel Performance Over Time",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

# Geographical analysis
st.header("Geographical Analysis")
# Country-based sales heatmap
country_sales = filtered_df.groupby("Country")[["Total Revenue", "Total Profit"]].sum().reset_index()
fig = px.scatter_geo(
    country_sales,
    locations="Country",
    locationmode="country names",
    size="Total Revenue",
    color="Total Profit",
    hover_name="Country",
    title="Sales and Profit by Country",
    projection="natural earth",
    color_continuous_scale=px.colors.sequential.Viridis
)
st.plotly_chart(fig, use_container_width=True)

# Correlation analysis
st.header("Correlation Analysis")
# Select only numerical columns
numeric_df = filtered_df.select_dtypes(include=[np.number])
# Remove ID columns
numeric_df = numeric_df.drop(columns=["Order ID", "Order Year", "Order Month"])

# Calculate correlation matrix
corr_matrix = numeric_df.corr()

# Plot heatmap
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", center=0, ax=ax)
plt.title("Correlation Matrix of Numerical Features")
st.pyplot(fig)

# Custom analysis: Profitability by order priority
st.header("Profitability by Order Priority")
priority_data = filtered_df.groupby("Order Priority")[["Total Revenue", "Total Profit", "Units Sold"]].sum().reset_index()
priority_data["Profit per Unit"] = priority_data["Total Profit"] / priority_data["Units Sold"]

fig = px.bar(
    priority_data,
    x="Order Priority",
    y="Profit per Unit",
    title="Average Profit per Unit by Order Priority",
    color="Order Priority",
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

# Delivery performance analysis
st.header("Delivery Performance Analysis")
delivery_stats = filtered_df.groupby("Region")["Delivery Time"].agg(["mean", "median", "min", "max"]).reset_index()
delivery_stats = delivery_stats.round(1)

fig = px.bar(
    delivery_stats,
    x="Region",
    y="mean",
    error_y="median",
    title="Average Delivery Time by Region (days)",
    color="Region",
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

# Add insights and conclusions
st.header("Key Insights")
st.markdown("""
Based on the analysis of the Amazon sales data, here are some key insights:

1. **Revenue Distribution**: The dashboard shows how sales are distributed across different regions and product categories.
2. **Profitability Analysis**: Certain product types yield higher profit margins than others.
3. **Time Series Trends**: The visualization reveals seasonal patterns and growth trends in sales.
4. **Regional Performance**: Some regions contribute significantly more to overall revenue and profits.
5. **Delivery Efficiency**: There are notable differences in delivery times across regions.

These insights can help in making data-driven decisions for inventory management, marketing strategies, and operational improvements.
""")

# App footer
st.markdown("---")
st.markdown("Amazon Sales Data Analysis Dashboard | Created with Streamlit")

# import streamlit as st
# import pandas as pd
# import numpy as np
# from sklearn.model_selection import train_test_split
# from sklearn.ensemble import RandomForestRegressor
# from sklearn.preprocessing import LabelEncoder
# import matplotlib.pyplot as plt

# # Load data
# df = pd.read_csv("Amazon Sales data.csv")

# # Preprocess data
# df = df.copy()
# df.drop(columns=['Order ID', 'Order Date', 'Ship Date'], inplace=True)

# # Encode categorical variables
# categorical_cols = ['Region', 'Country', 'Item Type', 'Sales Channel', 'Order Priority']
# label_encoders = {}
# for col in categorical_cols:
#     le = LabelEncoder()
#     df[col] = le.fit_transform(df[col])
#     label_encoders[col] = le

# # Features and target
# X = df.drop(columns=['Total Profit'])
# y = df['Total Profit']

# # Split and train model
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
# model = RandomForestRegressor(n_estimators=100, random_state=42)
# model.fit(X_train, y_train)

# # Streamlit app
# st.title("Amazon Sales Profit Predictor")
# st.write("Enter sales information to predict profit:")

# # Sidebar inputs
# input_data = {}
# for col in categorical_cols:
#     options = label_encoders[col].classes_
#     choice = st.selectbox(f"{col}", options)
#     input_data[col] = label_encoders[col].transform([choice])[0]

# input_data['Units Sold'] = st.number_input("Units Sold", value=1000)
# input_data['Unit Price'] = st.number_input("Unit Price", value=100.0)
# input_data['Unit Cost'] = st.number_input("Unit Cost", value=50.0)
# input_data['Total Revenue'] = input_data['Units Sold'] * input_data['Unit Price']
# input_data['Total Cost'] = input_data['Units Sold'] * input_data['Unit Cost']

# input_df = pd.DataFrame([input_data])
# predicted_profit = model.predict(input_df)[0]

# st.subheader(f"Predicted Profit: ${predicted_profit:,.2f}")

# # Feature importance plot
# st.subheader("Feature Importance")
# importances = model.feature_importances_
# features = X.columns
# indices = np.argsort(importances)[::-1]

# fig, ax = plt.subplots()
# ax.barh(range(len(features)), importances[indices])
# ax.set_yticks(range(len(features)))
# ax.set_yticklabels(features[indices])
# ax.invert_yaxis()
# st.pyplot(fig)
