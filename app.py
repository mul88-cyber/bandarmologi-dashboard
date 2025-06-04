import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard Big Player IDX", layout="wide")

@st.cache_data
def load_data():
    FILE_ID = "1Pw_3C6EJvzEYsVHagbu7tL5szit6kitl"
    CSV_URL = f"https://drive.google.com/uc?id={FILE_ID}"
    df = pd.read_csv(CSV_URL)

    # Normalisasi nama kolom & parsing tanggal
    df.columns = [c.strip() for c in df.columns]
    if "Last Trading Date" in df.columns:
        df.rename(columns={"Last Trading Date": "Date"}, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)

    # Pastikan semua kolom numerik terkonversi
    num_cols = ["Foreign Buy", "Foreign Sell", "High", "Low", "Close", "Open Price", "Previous", "Volume"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df.dropna(subset=["Date", "Stock Code", "Close", "Volume", "Foreign Buy", "Foreign Sell", "Previous", "Open Price"], inplace=True)
    return df

df = load_data()
if df.empty:
    st.error("Data gagal dimuat. Periksa file CSV di Google Drive.")
    st.stop()

# Hitung indikator teknikal
df["Net Foreign"] = df["Foreign Buy"] - df["Foreign Sell"]
df["Typical Price"] = (df["High"] + df["Low"] + df["Close"]) / 3
df["VWAP"] = (df["Typical Price"] * df["Volume"]).cumsum() / df["Volume"].cumsum()
delta = df["Close"].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()
rs = avg_gain / avg_loss
df["RSI"] = 100 - (100 / (1 + rs))
df["Change"] = df["Close"] - df["Previous"]
df["Change %"] = df["Change"] / df["Previous"].replace(0, pd.NA) * 100
df["Price Change %"] = (df["Close"] - df["Open Price"]) / df["Open Price"].replace(0, pd.NA) * 100

# ---------------------
st.title(":chart_with_upwards_trend: Dashboard Analisa Big Player (Bandarmologi)")

# --- Top Net Buy ---
st.header("🧲 Top Saham Net Buy Asing")
now = df["Date"].max()
periode = st.selectbox("Pilih periode", ["All Time", "3 Bulan Terakhir", "1 Bulan Terakhir"])
if periode == "3 Bulan Terakhir":
    df_filtered = df[df["Date"] >= now - timedelta(days=90)]
elif periode == "1 Bulan Terakhir":
    df_filtered = df[df["Date"] >= now - timedelta(days=30)]
else:
    df_filtered = df.copy()

top_buy = (
    df_filtered.groupby("Stock Code")
    .agg({
        "Company Name": "first",
        "Net Foreign": "sum",
        "Volume": "sum",
        "Close": "last"
    })
    .reset_index()
)
top_buy = top_buy.sort_values(by="Net Foreign", ascending=False).head(10)

st.dataframe(top_buy.style.format({
    "Net Foreign": "{:,.0f}",
    "Volume": "{:,.0f}",
    "Close": "{:,.0f}"
}))
fig1 = px.bar(top_buy, x="Stock Code", y="Net Foreign", title=f"Top Net Foreign Buy - {periode}")
st.plotly_chart(fig1, use_container_width=True)

# --- Deteksi Akumulasi ---
st.header("🔍 Deteksi Akumulasi (Volume Naik, Harga Sideways)")
akumulasi = df[(df["Volume"] > df["Volume"].rolling(5).mean()) & (df["Price Change %"].abs() < 2)]
akumulasi_top = (
    akumulasi.groupby("Stock Code")
    .agg({"Volume": "mean", "Price Change %": "mean", "Net Foreign": "sum"})
    .reset_index()
    .sort_values(by="Volume", ascending=False)
    .head(10)
)
st.dataframe(akumulasi_top.style.format({"Volume": "{:,.0f}", "Price Change %": "{:.2f}", "Net Foreign": "{:,.0f}"}))
fig_aku = px.bar(akumulasi_top, x="Stock Code", y="Volume", title="Top 10 Saham Akumulasi - Rata2 Volume Tinggi, Harga Sideways")
st.plotly_chart(fig_aku, use_container_width=True)

# --- Foreign Flow ---
st.header("🌍 Foreign Flow Harian per Saham")
selected_ff = st.selectbox("Pilih saham untuk melihat foreign flow harian", df["Stock Code"].unique())
unique_months = sorted(df["Date"].dt.to_period("M").unique(), reverse=True)
selected_month = st.selectbox("Pilih bulan", [str(m) for m in unique_months])
month_df = df[(df["Stock Code"] == selected_ff) & (df["Date"].dt.to_period("M") == pd.Period(selected_month))]
fig_ff = px.line(month_df.sort_values("Date"), x="Date", y="Net Foreign", title=f"Foreign Flow Harian - {selected_ff} ({selected_month})", markers=True)
st.plotly_chart(fig_ff, use_container_width=True)

# --- VWAP & RSI ---
st.header("📈 VWAP & RSI")
selected_stock = st.selectbox("Pilih saham untuk lihat VWAP & RSI", df["Stock Code"].unique(), key="vwap")
vwap_data = df[df["Stock Code"] == selected_stock].copy().reset_index(drop=True)
fig_vwap = px.line(vwap_data, x="Date", y=["Close", "VWAP"], labels={"value": "Harga", "Date": "Tanggal"}, title=f"{selected_stock} - Harga vs VWAP")
st.plotly_chart(fig_vwap, use_container_width=True)
fig_rsi = px.line(vwap_data, x="Date", y="RSI", labels={"value": "RSI", "Date": "Tanggal"}, title=f"{selected_stock} - RSI 14 Hari")
st.plotly_chart(fig_rsi, use_container_width=True)

# --- Watchlist ---
st.header("⭐ Watchlist Saham")
watchlist = st.multiselect("Pilih saham yang ingin dimonitor", df["Stock Code"].unique())
if watchlist:
    filtered_watchlist = df[df["Stock Code"].isin(watchlist)]
    st.dataframe(filtered_watchlist[["Date", "Stock Code", "Close", "Volume", "Net Foreign", "VWAP", "RSI"]].sort_values(by="Date", ascending=False).style.format({
        "Close": "{:,.0f}", "Volume": "{:,.0f}", "Net Foreign": "{:,.0f}", "VWAP": "{:,.0f}", "RSI": "{:,.1f}"
    }))
    csv = filtered_watchlist.to_csv(index=False).encode('utf-8')
    st.download_button("📂 Download Watchlist sebagai CSV", data=csv, file_name="watchlist.csv", mime="text/csv")
else:
    st.info("Pilih minimal satu saham untuk menampilkan watchlist.")

# --- Alert Harian ---
st.header("📢 Alert Harian (Volume, Net Foreign, Harga)")
latest_date = df["Date"].max()
latest_df = df[df["Date"] == latest_date].copy()
latest_df.dropna(subset=["Volume", "Net Foreign", "Change %"], inplace=True)
alerts = latest_df[
    (latest_df["Volume"] > latest_df["Volume"].median() * 2) |
    (latest_df["Net Foreign"].abs() > latest_df["Net Foreign"].median() * 2) |
    (latest_df["Change %"].abs() > 5)
]
st.dataframe(alerts[["Date", "Stock Code", "Volume", "Net Foreign", "Change %"]].sort_values(by="Net Foreign", ascending=False).style.format({
    "Volume": "{:,.0f}", "Net Foreign": "{:,.0f}", "Change %": "{:.2f}%"
}))

# --- Integrasi Multi Hari ---
st.header("🔁 Integrasi Multi Hari (5 Hari Terakhir)")
cutoff = df["Date"].max() - timedelta(days=5)
multi_df = df[df["Date"] >= cutoff]
summary_multi = (
    multi_df.groupby("Stock Code")
    .agg({
        "Net Foreign": "mean",
        "Volume": "mean",
        "Close": ["first", "last"]
    })
    .reset_index()
)
summary_multi.columns = ["Stock Code", "Net Foreign Avg", "Volume Avg", "Close First", "Close Last"]
summary_multi["Change 5D %"] = (summary_multi["Close Last"] - summary_multi["Close First"]) / summary_multi["Close First"] * 100
summary_multi = summary_multi.sort_values(by="Net Foreign Avg", ascending=False).head(10)
st.dataframe(summary_multi.style.format({
    "Net Foreign Avg": "{:,.0f}", "Volume Avg": "{:,.0f}", "Change 5D %": "{:.2f}%"
}))
