
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
import tensorflow as tf

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Input
from tensorflow.keras.callbacks import EarlyStopping

# =========================
# 1. CẤU HÌNH ỨNG DỤNG
# =========================
st.set_page_config(
    page_title="Dự báo giá cổ phiếu VNM",
    page_icon="📈",
    layout="wide"
)

st.title("📈 DỰ BÁO GIÁ CỔ PHIẾU BẰNG LSTM")
st.write("Dự báo giá đóng cửa cổ phiếu bằng mô hình Deep Learning.")

# Cố định seed
seed = 42
np.random.seed(seed)
tf.random.set_seed(seed)
random.seed(seed)


# =========================
# 2. HÀM TẠO CHUỖI DỮ LIỆU
# =========================
def create_sequences(data, window_size=60):
    X, y = [], []

    for i in range(window_size, len(data)):
        X.append(data[i - window_size:i])
        y.append(data[i])

    return np.array(X), np.array(y)


# =========================
# 3. THANH CÀI ĐẶT
# =========================
st.sidebar.header("Cài đặt mô hình")

ticker = st.sidebar.text_input(
    "Mã cổ phiếu Yahoo Finance",
    value="VNM.VN"
).strip().upper()

start_date = st.sidebar.date_input(
    "Ngày bắt đầu",
    value=pd.to_datetime("2018-01-01").date()
)

end_date = st.sidebar.date_input(
    "Ngày kết thúc",
    value=pd.Timestamp.today().date()
)

window_size = st.sidebar.number_input(
    "Số phiên nhìn lại",
    min_value=10,
    max_value=180,
    value=60
)

epochs = st.sidebar.number_input(
    "Số epochs",
    min_value=1,
    max_value=100,
    value=10
)

forecast_days = st.sidebar.number_input(
    "Số phiên muốn dự báo",
    min_value=1,
    max_value=30,
    value=10
)

run_button = st.sidebar.button(
    "Chạy mô hình",
    type="primary"
)


# =========================
# 4. TẢI DỮ LIỆU
# =========================
if run_button:

    if not ticker:
        st.error("Vui lòng nhập mã cổ phiếu.")
        st.stop()

    if start_date >= end_date:
        st.error("Ngày bắt đầu phải trước ngày kết thúc.")
        st.stop()

    with st.spinner("Đang tải dữ liệu..."):

        try:
            df = yf.download(
                ticker,
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                auto_adjust=False,
                progress=False
            )

            if df.empty:
                st.error("Không tải được dữ liệu. Hãy kiểm tra mã cổ phiếu.")
                st.stop()

            # Xử lý cột MultiIndex của yfinance
            if isinstance(df.columns, pd.MultiIndex):
                close_columns = [
                    col for col in df.columns
                    if col[0] == "Close"
                ]

                if not close_columns:
                    st.error("Không tìm thấy cột giá đóng cửa.")
                    st.stop()

                close = df[close_columns[0]]

            else:
                close = df["Close"]

            data = pd.DataFrame({
                "Close": pd.to_numeric(close, errors="coerce")
            }).dropna()

        except Exception as e:
            st.error(f"Lỗi tải dữ liệu: {e}")
            st.stop()

    if len(data) <= int(window_size) + 20:
        st.error("Dữ liệu không đủ để huấn luyện mô hình.")
        st.stop()

    st.subheader("1. Dữ liệu lịch sử")

    col1, col2, col3 = st.columns(3)

    col1.metric("Số phiên giao dịch", len(data))
    col2.metric("Giá đóng cửa gần nhất", f"{data['Close'].iloc[-1]:,.2f}")
    col3.metric("Mã cổ phiếu", ticker)

    st.line_chart(data["Close"])

    # =========================
    # 5. CHIA TẬP TRAIN VÀ TEST
    # =========================
    values = data[["Close"]].values

    train_size = int(0.8 * len(values))

    train_data = values[:train_size]
    test_data = values[train_size:]

    scaler = MinMaxScaler()

    train_scaled = scaler.fit_transform(train_data)
    test_scaled = scaler.transform(test_data)

    X_train, y_train = create_sequences(
        train_scaled, int(window_size)
    )

    test_combined = np.vstack([
        train_scaled[-int(window_size):],
        test_scaled
    ])

    X_test, y_test = create_sequences(
        test_combined, int(window_size)
    )

    # Tách validation theo thứ tự thời gian
    val_size = max(1, int(0.1 * len(X_train)))

    X_val = X_train[-val_size:]
    y_val = y_train[-val_size:]

    X_train_final = X_train[:-val_size]
    y_train_final = y_train[:-val_size]

    if len(X_train_final) == 0:
        st.error("Không đủ dữ liệu để tạo tập huấn luyện.")
        st.stop()

    # =========================
    # 6. XÂY DỰNG MÔ HÌNH LSTM
    # =========================
    model = Sequential([
        Input(shape=(int(window_size), 1)),
        LSTM(50, return_sequences=True),
        LSTM(50),
        Dense(1)
    ])

    model.compile(
        optimizer="adam",
        loss="mean_squared_error"
    )

    early_stop = EarlyStopping(
        monitor="val_loss",
        patience=5,
        restore_best_weights=True
    )

    st.subheader("2. Huấn luyện mô hình")

    progress = st.progress(0)
    status = st.empty()

    class StreamlitProgress(tf.keras.callbacks.Callback):
        def on_epoch_end(self, epoch, logs=None):
            progress.progress(
                min(1.0, (epoch + 1) / int(epochs))
            )
            status.write(
                f"Epoch {epoch + 1}/{int(epochs)}"
                f" | Loss: {logs.get('loss', 0):.6f}"
                f" | Val Loss: {logs.get('val_loss', 0):.6f}"
            )

    with st.spinner("Mô hình đang học từ dữ liệu..."):

        history = model.fit(
            X_train_final,
            y_train_final,
            validation_data=(X_val, y_val),
            epochs=int(epochs),
            batch_size=32,
            shuffle=False,
            callbacks=[
                early_stop,
                StreamlitProgress()
            ],
            verbose=0
        )

    st.success("Huấn luyện hoàn tất!")

    # =========================
    # 7. ĐÁNH GIÁ MÔ HÌNH
    # =========================
    test_pred_scaled = model.predict(X_test, verbose=0)

    test_pred = scaler.inverse_transform(test_pred_scaled)

    y_test_real = scaler.inverse_transform(
        y_test.reshape(-1, 1)
    )

    rmse = np.sqrt(
        mean_squared_error(y_test_real, test_pred)
    )

    mae = mean_absolute_error(
        y_test_real, test_pred
    )

    r2 = r2_score(y_test_real, test_pred)

    st.subheader("3. Đánh giá mô hình")

    col1, col2, col3 = st.columns(3)

    col1.metric("RMSE", f"{rmse:.3f}")
    col2.metric("MAE", f"{mae:.3f}")
    col3.metric("R²", f"{r2:.4f}")

    st.caption(
        "RMSE và MAE đo sai số dự báo; giá trị thấp thường tốt hơn. "
        "R² càng gần 1 thường cho thấy mô hình phù hợp hơn trên tập đánh giá."
    )

    # =========================
    # 8. BIỂU ĐỒ LOSS
    # =========================
    st.subheader("4. Biểu đồ Train Loss và Validation Loss")

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.plot(history.history["loss"], label="Train Loss")
    ax.plot(history.history["val_loss"], label="Validation Loss")

    ax.set_xlabel("Epoch")
    ax.set_ylabel("MSE")
    ax.set_title("Loss Train vs Validation")
    ax.legend()
    ax.grid(True, alpha=0.3)

    st.pyplot(fig)
    plt.close(fig)

    # =========================
    # 9. SO SÁNH GIÁ THẬT VÀ DỰ BÁO
    # =========================
    st.subheader("5. Giá thực tế và giá dự báo trên tập Test")

    test_dates = data.index[train_size:]

    comparison = pd.DataFrame(
        {
            "Giá thật": y_test_real.flatten(),
            "Giá dự báo": test_pred.flatten()
        },
        index=test_dates
    )

    st.line_chart(comparison)

    with st.expander("Xem bảng kết quả Test"):
        st.dataframe(comparison, use_container_width=True)

    # =========================
    # 10. DỰ BÁO TƯƠNG LAI
    # =========================
    st.subheader(
        f"6. Dự báo {int(forecast_days)} phiên tiếp theo"
    )

    all_scaled = scaler.transform(values)

    last_window = all_scaled[-int(window_size):].reshape(
        1, int(window_size), 1
    )

    future_predictions = []

    for _ in range(int(forecast_days)):

        next_pred = model.predict(
            last_window, verbose=0
        )

        future_predictions.append(next_pred[0, 0])

        last_window = np.concatenate(
            [
                last_window[:, 1:, :],
                next_pred.reshape(1, 1, 1)
            ],
            axis=1
        )

    future_predictions = scaler.inverse_transform(
        np.array(future_predictions).reshape(-1, 1)
    ).flatten()

    future_dates = pd.bdate_range(
        start=data.index[-1] + pd.Timedelta(days=1),
        periods=int(forecast_days)
    )

    future_df = pd.DataFrame({
        "Ngày dự kiến": future_dates.strftime("%d/%m/%Y"),
        "Giá đóng cửa dự báo": future_predictions
    })

    st.dataframe(future_df, use_container_width=True)

    # =========================
    # 11. BIỂU ĐỒ DỰ BÁO
    # =========================
    st.subheader("7. Biểu đồ dự báo tương lai")

    fig, ax = plt.subplots(figsize=(12, 5))

    recent_n = min(60, len(data))

    ax.plot(
        data.index[-recent_n:],
        data["Close"].iloc[-recent_n:],
        label="Giá lịch sử"
    )

    ax.plot(
        future_dates,
        future_predictions,
        marker="o",
        linestyle="--",
        label="Giá dự báo"
    )

    ax.set_title(f"Dự báo giá cổ phiếu {ticker}")
    ax.set_xlabel("Ngày")
    ax.set_ylabel("Giá đóng cửa")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.autofmt_xdate()

    st.pyplot(fig)
    plt.close(fig)

    # =========================
    # 12. TẢI KẾT QUẢ
    # =========================
    csv = future_df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="📥 Tải kết quả dự báo CSV",
        data=csv,
        file_name="du_bao_co_phieu.csv",
        mime="text/csv"
    )

    st.warning(
        "Dự báo chỉ dựa trên giá đóng cửa lịch sử. "
        "Kết quả có thể sai lệch đáng kể và không phải "
        "khuyến nghị mua hoặc bán cổ phiếu."
    )

else:
    st.info(
        "Nhập thông số ở thanh bên trái rồi nhấn "
        "**Chạy mô hình** để bắt đầu."
    )
