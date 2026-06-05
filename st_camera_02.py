import streamlit as st
from PIL import Image

#import cv2



st.title("🖼️ Upload an Image 📸")
uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "bmp", "webp"])
if uploaded:
    image = Image.open(uploaded)
    st.image(image, caption=uploaded.name, use_container_width=True)
    st.write(f"Size: {image.size} | Mode: {image.mode}")


st.title("📸 Camera")

# --- Capture ---
img_file = st.camera_input("Take a photo")

if img_file is not None:

    # ── Display original ──────────────────────────────────────────
    st.subheader("Original")
    st.image(img_file, use_container_width=True)


