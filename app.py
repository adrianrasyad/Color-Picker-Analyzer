import streamlit as st
import cv2
import numpy as np
import matplotlib.pyplot as plt
from streamlit_image_coordinates import streamlit_image_coordinates

# Tambahkan helper untuk deteksi mobile
def is_mobile():
    # Streamlit tidak punya deteksi device, pakai lebar window
    return st.session_state.get("window_width", 1200) < 768

# Inject JS untuk update lebar window ke session_state
st.markdown("""
<script>
    const sendWidth = () => {
        window.parent.postMessage({streamlitSetFrameHeight: document.body.scrollHeight}, "*");
        window.parent.postMessage({type: "streamlit:setComponentValue", value: window.innerWidth}, "*");
        window.localStorage.setItem("window_width", window.innerWidth);
    };
    window.addEventListener("resize", sendWidth);
    sendWidth();
</script>
""", unsafe_allow_html=True)

# Ambil lebar window dari localStorage (via JS di atas)
window_width = st.query_params.get("window_width", 1200)
try:
    st.session_state["window_width"] = int(window_width)
except:
    st.session_state["window_width"] = 1200

# Konfigurasi halaman: layout wide agar tampilan lebih luas dan judul
st.set_page_config(layout="wide", page_title="Color Picker & Analyzer")
st.title("🎨 Penganalisis Warna Gambar Interaktif")
st.markdown("Unggah gambar, lalu **klik** pada warna di gambar untuk menampilkan kode warna dan menganalisis distribusinya.")

# Bagian Unggah Gambar
st.subheader("Unggah Gambar")
uploaded_file = st.file_uploader("Drag and drop file here", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

# Tambahkan CSS agar gambar dan container full width di mobile
st.markdown("""
<style>
@media (max-width: 768px) {
    .element-container:has(img) {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    img {
        width: 100% !important;
        height: auto !important;
        display: block;
        margin: 0 auto;
        border-radius: 10px;
    }
}
</style>
""", unsafe_allow_html=True)

# Logika Pemrosesan Gambar
if uploaded_file is not None:
    # Membaca file gambar
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if image_bgr is None:
        st.error("File yang diunggah bukan gambar yang valid.")
        st.stop()
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    # --- Layout Responsif ---
    if is_mobile():
        st.subheader("Klik Gambar untuk Deteksi Warna")
        # Tampilkan gambar full width di mobile
        value = streamlit_image_coordinates(
            image_rgb,
            key="image_click",
            width=st.session_state["window_width"] - 32  # padding dikurangi
        )
        st.subheader("Hasil Deteksi Piksel")
        info_container = st.container()
    else:
        # Dua kolom di desktop/tablet
        col_img, col_info = st.columns([2, 1])
        with col_img:
            st.subheader("Klik Gambar untuk Deteksi Warna")
            value = streamlit_image_coordinates(
                image_rgb,
                key="image_click",
                width=700  # atau sesuaikan dengan kebutuhan desktop
            )
        info_container = col_info

    # --- Kolom Hasil Deteksi Piksel ---
    with info_container:
        st.subheader("Hasil Deteksi Piksel")

        # Perbaikan Logika: Jika tidak ada klik terdeteksi (klik di luar area gambar)
        if value is None:
            st.info("👈 Silakan klik suatu titik **di dalam gambar** di samping.")
        else:
            # Koordinat yang diklik (x, y)
            x = value['x']
            y = value['y']

            # Cek apakah koordinat valid (di dalam batas dimensi gambar)
            if 0 <= y < image_rgb.shape[0] and 0 <= x < image_rgb.shape[1]:
                # Ambil nilai RGB pada koordinat (y, x)
                r, g, b = image_rgb[y, x]

                # Konversi RGB ke HEX
                hex_color = '#{:02x}{:02x}{:02x}'.format(r, g, b)

                # 1. Kotak Warna (Visualisasi)
                st.markdown("#### Preview Warna")
                st.markdown(
                    f'<div style="width: 100%; height: 50px; background-color: {hex_color}; border: 1px solid #ccc; border-radius: 5px;"></div>',
                    unsafe_allow_html=True
                )
                
                st.write(f"**Piksel Klik:** ({x}, {y})")

                # 2. Metrik Kode Warna
                col_hex, col_rgb = st.columns(2)
                with col_hex:
                    st.metric("HEX", hex_color)
                with col_rgb:
                    st.metric("RGB", f"({r}, {g}, {b})")
                    
                # 3. Bar Chart Nilai Intensitas
                st.markdown("#### Nilai Intensitas RGB")
                
                # Membuat bar chart sederhana untuk nilai RGB
                fig, ax = plt.subplots(figsize=(4, 2))
                colors = ['red', 'green', 'blue']
                ax.bar(['R', 'G', 'B'], [r, g, b], color=colors)
                ax.set_ylim(0, 255)
                ax.set_title("Intensitas Piksel")
                st.pyplot(fig)
                plt.close(fig)
            else:
                # Pesan ini jarang muncul karena perbaikan logika sebelumnya, tapi tetap sebagai jaga-jaga
                st.warning("Klik di luar batas gambar yang valid.")

    

    # --- Bagian Analisis Keseluruhan (Histogram) ---
    st.subheader("Analisis Histogram Seluruh Gambar")
    
    # Membuat figure untuk histogram
    fig_hist, ax_hist = plt.subplots(figsize=(6 if is_mobile() else 10, 3 if is_mobile() else 4))
    
    # Menghitung Histogram untuk setiap channel (R, G, B)
    for i, color in enumerate(['R', 'G', 'B']):
        # Histogram dihitung
        hist = cv2.calcHist([image_rgb], [i], None, [256], [0, 256])
        # Plotting
        ax_hist.plot(hist, color=color.lower(), label=color)
        
    ax_hist.set_title("Histogram Distribusi Warna")
    ax_hist.set_xlabel("Intensitas")
    ax_hist.set_ylabel("Jumlah Piksel")
    ax_hist.legend()
    
    st.pyplot(fig_hist)
    plt.close(fig_hist)

    # --- Grid Sampel Warna Modern ---
    st.subheader("🟩 Grid Sampel Warna Otomatis")
    step = st.slider("Jarak sampling grid (px)", min_value=5, max_value=100, value=25, step=1)
    rows = list(range(0, image_rgb.shape[0], step))
    cols = list(range(0, image_rgb.shape[1], step))

    # Buat grid warna (list of list)
    grid_hex = []
    for y in rows:
        row_hex = []
        for x in cols:
            r, g, b = image_rgb[y, x]
            hex_color = '#{:02X}{:02X}{:02X}'.format(r, g, b)
            row_hex.append(hex_color)
        grid_hex.append(row_hex)

    # Tampilkan grid warna dengan preview kotak warna
    def color_cell(hex_color):
        size = "28px" if is_mobile() else "40px"
        return f'''
        <div style="background:{hex_color};width:{size};height:{size};display:flex;align-items:center;justify-content:center;border-radius:6px;border:1px solid #eee;">
            <span style="color:#222;font-size:10px;font-family:monospace;text-shadow:0 1px 2px #fff;">{hex_color}</span>
        </div>
        '''

    # Buat HTML grid
    html = '<div style="overflow-x:auto;"><table style="border-collapse:collapse;"><tr><th></th>'
    for x in cols:
        html += f'<th style="padding:2px 4px;font-size:11px;color:#888;">{x}</th>'
    html += '</tr>'
    for i, y in enumerate(rows):
        html += f'<tr><th style="padding:2px 4px;font-size:11px;color:#888;">{y}</th>'
        for j, x in enumerate(cols):
            html += f'<td style="padding:2px;">{color_cell(grid_hex[i][j])}</td>'
        html += '</tr>'
    html += '</table></div>'

    st.markdown(html, unsafe_allow_html=True)
    st.caption(f"Grid warna otomatis • sampling tiap {step}px • Kolom = X, Baris = Y.")

    # Tombol unduh CSV warna
    import pandas as pd
    df_grid = pd.DataFrame(grid_hex, index=rows, columns=cols)
    csv = df_grid.to_csv()
    st.download_button("⬇️ Unduh CSV warna grid", csv, file_name="grid_warna.csv", mime="text/csv")
