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

# Hitung RSI
delta = df["Close"].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()
rs = avg_gain / avg_loss
df["RSI"] = 100 - (100 / (1 + rs))

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

selected_stock = st.selectbox("Pilih saham untuk lihat VWAP & RSI", df["Stock Code"].unique())
vwap_data = df[df["Stock Code"] == selected_stock].copy()
vwap_data.reset_index(drop=True, inplace=True)

fig_vwap = px.line(vwap_data, y=["Close", "VWAP"],
                   labels={"value": "Harga", "index": "Hari ke-"},
                   title=f"{selected_stock} - Harga vs VWAP")
st.plotly_chart(fig_vwap, use_container_width=True)

# RSI Chart
st.subheader("📉 RSI (Relative Strength Index)")
fig_rsi = px.line(vwap_data, y="RSI", labels={"value": "RSI", "index": "Hari ke-"},
                  title=f"{selected_stock} - RSI 14 Hari")
st.plotly_chart(fig_rsi, use_container_width=True)

# ⭐ Watchlist Saham
st.subheader("⭐ Watchlist Saham")
watchlist = st.multiselect("Pilih saham yang ingin dimonitor", df["Stock Code"].unique())

if watchlist:
    filtered_watchlist = df[df["Stock Code"].isin(watchlist)]
    st.dataframe(
        filtered_watchlist[["Stock Code", "Close", "Volume", "Net Foreign", "VWAP", "RSI"]]
        .sort_values(by="Net Foreign", ascending=False)
    )
else:
    st.info("Pilih minimal satu saham untuk menampilkan watchlist.")

