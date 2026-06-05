
from pathlib import Path

import streamlit as st
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

st.set_page_config(page_title="📸 Image Browser 📸", layout="wide")
st.title("Image Browser")

# --- Session state ---
if "current_dir" not in st.session_state:
    st.session_state.current_dir = Path.cwd()

current_dir = Path(st.session_state.current_dir)
if not current_dir.is_dir():
    current_dir = Path.cwd()
    st.session_state.current_dir = current_dir

# --- Path bar ---
st.caption(f"Current directory: `{current_dir}`")

# --- Navigation: go up ---
at_root = current_dir.parent == current_dir
if not at_root:
    if st.button("Go up"):
        st.session_state.current_dir = current_dir.parent
        st.rerun()

# --- Split view: left = browser, right = image ---
left, right = st.columns([1, 2])

with left:
    # Subdirectories
    subdirs = sorted(p for p in current_dir.iterdir() if p.is_dir())
    if subdirs:
        st.subheader("Folders")
        for d in subdirs:
            if st.button(f"[ {d.name} ]", key=f"dir_{d}", use_container_width=True):
                st.session_state.current_dir = d
                st.rerun()

    # Image files
    image_paths = sorted(p for p in current_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    if image_paths:
        st.subheader("Images")
        selected = st.radio(
            "Pick an image:",
            options=image_paths,
            format_func=lambda p: p.name,
            label_visibility="collapsed",
        )
    else:
        selected = None
        st.info("No images in this folder.")

with right:
    if selected is not None:
        width = st.slider("Display width", min_value=100, max_value=2500, value=700)
        image = Image.open(selected)
        st.image(
            image,
            width=width,
            caption=f"{selected.name}  |  {image.size[0]} x {image.size[1]}  |  {image.mode}",
        )
