import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Big Player IDX", layout="wide")

# Load data dari Google Drive
FILE_ID = "1Pw_3C6EJvzEYsVHagbu7tL5szit6kitl"
CSV_URL = f"https://drive.google.com/uc?id={FILE_ID}"
df = pd.read_csv(CSV_URL)

# Hitung Net Foreign
df["Net Foreign"] = df["Foreign Buy"] - df["Foreign Sell"]

# Hitung VWAP
df["Typical Price"] = (df["High"] + df["Low"] + df["Close"]) / 3
df["VWAP"] = (df["Typical Price"] * df["Volume"]).cumsum() / df["Volume"].cumsum()

st.title("📊 Dashboard Analisa Big Player (Bandarmologi)")

# Top Net Buy
st.subheader("🧠 Top 10 Saham Net Buy Asing")
top_foreign = df.sort_values(by="Net Foreign", ascending=False).head(10)
st.dataframe(top_foreign[["Stock Code", "Company Name", "Net Foreign", "Volume", "Close"]])

fig1 = px.bar(top_foreign, x="Stock Code", y="Net Foreign", title="Top Net Foreign Buy")
st.plotly_chart(fig1, use_container_width=True)

# Filter Akumulasi: volume tinggi tapi harga stagnan
st.subheader("🔍 Deteksi Akumulasi (Volume Naik, Harga Sideways)")
df["Price Change %"] = (df["Close"] - df["Open Price"]) / df["Open Price"] * 100
accumulated = df[(df["Volume"] > df["Volume"].median()) & (df["Price Change %"].abs() < 2)]
st.dataframe(accumulated[["Stock Code", "Volume", "Close", "Price Change %"]].sort_values(by="Volume", ascending=False).head(10))

# Transaksi Non Reguler
st.subheader("📦 Saham dengan Transaksi Non-Regular")
non_reg = df[df["Non Regular Volume"] > 0]
st.dataframe(non_reg[["Stock Code", "Non Regular Volume", "Non Regular Value"]].sort_values(by="Non Regular Value", ascending=False).head(10))

# VWAP Chart
st.subheader("📈 VWAP Chart (Harga vs VWAP)")

# Dropdown untuk memilih saham
selected_stock = st.selectbox("Pilih saham untuk lihat VWAP", df["Stock Code"].unique())

# Filter data untuk saham terpilih
vwap_data = df[df["Stock Code"] == selected_stock].copy()
vwap
