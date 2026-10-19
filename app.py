import streamlit as st
import pandas as pd

st.title("UAC Care Load Analytics")

# load the data
df = pd.read_csv("HHS_Unaccompanied_Alien_Children_Program.csv")
df.columns = ["Date", "Apprehended", "CBP", "Transferred", "HHS", "Discharged"]
df = df.dropna(how="all")                       # remove empty rows
df["Date"] = pd.to_datetime(df["Date"])
df["HHS"] = df["HHS"].astype(str).str.replace(",", "").astype(float)
df = df.sort_values("Date").set_index("Date")

# new columns
df["Total Load"] = df["CBP"] + df["HHS"]
df["Net Intake"] = df["Transferred"] - df["Discharged"]
df["Load 7-day avg"] = df["Total Load"].rolling("7D").mean()
df["Load 14-day avg"] = df["Total Load"].rolling("14D").mean()
df["Growth %"] = df["Total Load"].pct_change() * 100
df.loc[df.index.to_series().diff().dt.days != 1, "Growth %"] = None   # only use days right after each other

# sidebar
st.sidebar.header("Filters")
start = st.sidebar.date_input("Start date", df.index.min())
end = st.sidebar.date_input("End date", df.index.max())
level = st.sidebar.selectbox("Time level", ["Daily", "Weekly", "Monthly"])
show = st.sidebar.multiselect("Columns to show", ["Total Load", "CBP", "HHS", "Net Intake", "Load 7-day avg", "Load 14-day avg"], default=["Total Load", "CBP", "HHS"])

data = df[(df.index >= pd.to_datetime(start)) & (df.index <= pd.to_datetime(end))]
if level == "Weekly":
    data = data.resample("W").mean()
elif level == "Monthly":
    data = data.resample("MS").mean()

# KPI cards
st.subheader("KPIs")
a, b, c, d, e = st.columns(5)
a.metric("Children under care (latest)", int(df["Total Load"].iloc[-1]))
b.metric("Avg net intake per day", round(df["Net Intake"].mean(), 1))
c.metric("Volatility (std of growth %)", round(df["Growth %"].std(), 2))
d.metric("Days with 7-day avg net intake > 0", str(round((df["Net Intake"].rolling("7D").mean() > 0).mean() * 100)) + "%")
e.metric("Discharges / transfers", round(df["Discharged"].sum() / df["Transferred"].sum(), 2))

st.subheader("System Load Overview")
if show:
    st.line_chart(data[show])

st.subheader("CBP vs HHS")
st.line_chart(data[["CBP", "HHS"]])

st.subheader("Net Intake")
st.bar_chart(data["Net Intake"])

st.subheader("Cumulative Net Intake (backlog)")
st.line_chart(data["Net Intake"].cumsum())

st.subheader("Data")
st.dataframe(data)
