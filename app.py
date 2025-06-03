# Candlestick Chart
st.subheader("📉 Grafik Candlestick")
selected_candle = st.selectbox("Pilih saham untuk candlestick", df["Stock Code"].unique())
candle_data = df[df["Stock Code"] == selected_candle].copy()
if not candle_data.empty:
    fig_candle = px.candlestick(
        candle_data,
        x=candle_data.index,
        open="Open Price",
        high="High",
        low="Low",
        close="Close",
        title=f"Candlestick Chart: {selected_candle}"
    )
    st.plotly_chart(fig_candle, use_container_width=True)
else:
    st.warning("Data tidak ditemukan.")
