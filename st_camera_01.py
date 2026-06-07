
import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io

st.title("📷 Single Frame Capture")

# --- Capture ---
img_file = st.camera_input("Take a photo")

if img_file is not None:

    # ── Display original ──────────────────────────────────────────
    st.subheader("Original")
    st.image(img_file, use_container_width=True)

    # ── PIL processing ────────────────────────────────────────────
    img_pil = Image.open(img_file)
    st.write(f"Size: {img_pil.size} | Mode: {img_pil.mode}")

    # ── OpenCV processing ─────────────────────────────────────────
    img_file.seek(0)                          # reset buffer after PIL read
    bytes_data = img_file.read()
    img_array  = np.frombuffer(bytes_data, np.uint8)
    img_cv     = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    # Convert to grayscale
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    st.subheader("Grayscale")
    st.image(gray, use_container_width=True, clamp=True)

    # Edge detection
    edges = cv2.Canny(gray, threshold1=50, threshold2=150)
    st.subheader("Edge Detection (Canny)")
    st.image(edges, use_container_width=True, clamp=True)

    # ── Download processed image ──────────────────────────────────
    _, buffer = cv2.imencode(".jpg", edges)
    st.download_button(
        label="⬇️ Download Edge Image",
        data=buffer.tobytes(),
        file_name="edges.jpg",
        mime="image/jpeg"
    )
