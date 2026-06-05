import streamlit as st
from PIL import Image

#import cv2



st.title("🔼 Upload an Image 🔼")

max_size = st.slider("Image size (px)", min_value=100, max_value=2400, value=1024, step=50)

uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "bmp", "webp"])
if uploaded:
    image = Image.open(uploaded)
    ratio = max_size / image.width
    new_height = int(image.height * ratio)
    image = image.resize((max_size, new_height), Image.LANCZOS)
    st.image(image, caption=uploaded.name, width=max_size)
    st.write(f"Size: {image.size} | Mode: {image.mode}")


st.title("📸 Camera 📸")

# --- Capture ---
img_file = st.camera_input("Take a photo")

if img_file is not None:

    # ── Display original ──────────────────────────────────────────
    st.subheader("Original")
    st.image(img_file, use_container_width=True)


