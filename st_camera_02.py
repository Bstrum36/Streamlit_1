import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import streamlit as st
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

st.title("🖼️ Image Directory Slideshow")

max_size = st.slider("Display width (px)", min_value=100, max_value=2400, value=1024, step=50)

if "folder" not in st.session_state:
    st.session_state.folder = ""

if st.button("📁 Select Directory"):
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", True)
    selected = filedialog.askdirectory(master=root)
    root.destroy()
    if selected:
        st.session_state.folder = selected

if st.session_state.folder:
    st.write(f"**Directory:** `{st.session_state.folder}`")

folder = st.session_state.folder

if folder:
    folder_path = Path(folder)
    images = sorted(p for p in folder_path.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    total = len(images)
    if not images:
        st.warning("No images found in that directory.")
    else:
        placeholder = st.empty()
        for idx, img_path in enumerate(images, start=1):
            image = Image.open(img_path)
            orig_size = image.size
            ratio = max_size / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_size, new_height), Image.LANCZOS)
            caption = f"{img_path.name}  |  Image {idx} of {total}  |  Size: {orig_size[0]}×{orig_size[1]} px"
            with placeholder.container():
                st.image(image, caption=caption, width=max_size)
            time.sleep(2)

