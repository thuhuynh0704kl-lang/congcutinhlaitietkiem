import streamlit as st

# =========================
# CẤU HÌNH TRANG
# =========================
st.set_page_config(
    page_title="Tính lãi tiền gửi tiết kiệm",
    page_icon="💰",
    layout="centered"
)

# =========================
# CSS GIAO DIỆN
# =========================
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 5px;
    }

    .sub-title {
        text-align: center;
        color: #666;
        margin-bottom: 25px;
    }

    .result-box {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #ddd;
        margin-bottom: 12px;
    }

    .result-label {
        font-size: 15px;
        color: #666;
    }

    .result-value {
        font-size: 23px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# TIÊU ĐỀ
# =========================
st.markdown(
    '<div class="main-title">💰 TÍNH LÃI TIỀN GỬI TIẾT KIỆM</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">Tính lãi đơn và lãi kép theo kỳ hạn gửi</div>',
    unsafe_allow_html=True
)

# =========================
# NHẬP THÔNG TIN
# =========================
st.subheader("📋 Thông tin tiền gửi")

so_tien = st.number_input(
    "Số tiền gửi (VNĐ)",
    min_value=0.0,
    value=100_000_000.0,
    step=1_000_000.0,
    format="%.0f"
)

ky_han = st.number_input(
    "Kỳ hạn (tháng)",
    min_value=1,
    max_value=600,
    value=12,
    step=1
)

loai_lai = st.selectbox(
    "Hình thức tính lãi",
    [
        "Lãi đơn",
        "Lãi kép"
    ]
)

hinh_thuc_nhan_lai = st.selectbox(
    "Hình thức nhận lãi",
    [
        "Lãnh lãi hàng tháng",
        "Lãnh lãi hàng quý",
        "Lãnh lãi cuối kỳ"
    ]
)

lai_suat_nam = st.number_input(
    "Lãi suất (%/năm)",
    min_value=0.0,
    max_value=100.0,
    value=6.0,
    step=0.01,
    format="%.2f"
)

# =========================
# NÚT TÍNH
# =========================
if st.button("🧮 TÍNH LÃI", use_container_width=True):

    # Kiểm tra dữ liệu
    if so_tien <= 0:
        st.error("Vui lòng nhập số tiền gửi lớn hơn 0.")
        st.stop()

    if lai_suat_nam < 0:
        st.error("Lãi suất không được nhỏ hơn 0.")
        st.stop()

    # Đổi lãi suất từ % sang số thập phân
    r = lai_suat_nam / 100

    # Kỳ hạn tính theo năm
    so_nam = ky_han / 12

    # =========================
    # LÃI ĐƠN
    # =========================
    if loai_lai == "Lãi đơn":

        # I = P × r × t
        tong_lai = so_tien * r * so_nam

        tong_tien = so_tien + tong_lai

        # Tính lãi theo kỳ nhận
        if hinh_thuc_nhan_lai == "Lãnh lãi hàng tháng":
            tien_lai_dinh_ky = so_tien * r / 12

        elif hinh_thuc_nhan_lai == "Lãnh lãi hàng quý":
            tien_lai_dinh_ky = so_tien * r / 4

        else:
            tien_lai_dinh_ky = tong_lai

    # =========================
    # LÃI KÉP
    # =========================
    else:

        if hinh_thuc_nhan_lai == "Lãnh lãi hàng tháng":

            # Lãi kép theo tháng
            so_ky = ky_han
            lai_suat_ky = r / 12

            tong_tien = so_tien * (1 + lai_suat_ky) ** so_ky
            tong_lai = tong_tien - so_tien

            # Lãi phát sinh trong tháng đầu tiên
            tien_lai_dinh_ky = so_tien * lai_suat_ky

        elif hinh_thuc_nhan_lai == "Lãnh lãi hàng quý":

            # Lãi kép theo quý
            so_ky = ky_han / 3
            lai_suat_ky = r / 4

            tong_tien = so_tien * (1 + lai_suat_ky) ** so_ky
            tong_lai = tong_tien - so_tien

            # Lãi phát sinh trong quý đầu tiên
            tien_lai_dinh_ky = so_tien * lai_suat_ky

        else:

            # Lãi kép cuối kỳ
            # Tính theo kỳ hạn tháng, ghép lãi hàng tháng
            so_ky = ky_han
            lai_suat_ky = r / 12

            tong_tien = so_tien * (1 + lai_suat_ky) ** so_ky
            tong_lai = tong_tien - so_tien

            tien_lai_dinh_ky = tong_lai

    # =========================
    # HIỂN THỊ KẾT QUẢ
    # =========================
    st.divider()
    st.subheader("📊 Kết quả")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "💵 Tiền lãi định kỳ",
            f"{tien_lai_dinh_ky:,.0f} VNĐ"
        )

    with col2:
        st.metric(
            "📈 Tổng tiền lãi",
            f"{tong_lai:,.0f} VNĐ"
        )

    st.metric(
        "💰 Tổng tiền gốc + lãi",
        f"{tong_tien:,.0f} VNĐ"
    )

    # =========================
    # THÔNG TIN TÓM TẮT
    # =========================
    st.divider()

    st.subheader("📝 Thông tin khoản gửi")

    st.write(f"**Số tiền gửi:** {so_tien:,.0f} VNĐ")
    st.write(f"**Kỳ hạn:** {ky_han} tháng ({so_nam:.2f} năm)")
    st.write(f"**Hình thức tính:** {loai_lai}")
    st.write(f"**Nhận lãi:** {hinh_thuc_nhan_lai}")
    st.write(f"**Lãi suất:** {lai_suat_nam:.2f}%/năm")

    # =========================
    # CÔNG THỨC
    # =========================
    with st.expander("📚 Xem công thức tính"):

        if loai_lai == "Lãi đơn":
            st.markdown("""
            **Công thức lãi đơn:**

            `I = P × r × t`

            Trong đó:

            - `P`: Số tiền gốc
            - `r`: Lãi suất/năm
            - `t`: Thời gian gửi (năm)
            - `I`: Tổng tiền lãi

            **Tổng tiền nhận được:**

            `A = P + I`
            """)

        else:
            st.markdown("""
            **Công thức lãi kép:**

            `A = P × (1 + r)ⁿ`

            Trong đó:

            - `P`: Số tiền gốc
            - `r`: Lãi suất mỗi kỳ
            - `n`: Số kỳ ghép lãi
            - `A`: Tổng tiền gốc + lãi

            **Tổng tiền lãi:**

            `I = A - P`
            """)

# =========================
# FOOTER
# =========================
st.divider()

st.caption(
    "💡 Lưu ý: Đây là công cụ tính toán mang tính tham khảo. "
    "Lãi suất thực tế của ngân hàng có thể áp dụng quy định và cách tính khác."
)
