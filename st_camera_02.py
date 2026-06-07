import os
import time
from pathlib import Path

import streamlit as st
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# --- Session state defaults ---
for key, val in [("current_dir", os.path.expanduser("~")),
                 ("running", False),
                 ("idx", 0)]:
    if key not in st.session_state:
        st.session_state[key] = val

# --- Sidebar: navigation + controls ---
with st.sidebar:
    st.header("📁 Navigate")

    current = st.session_state.current_dir

    # Breadcrumb buttons
    parts = Path(current).parts
    for i, part in enumerate(parts):
        crumb_path = str(Path(*parts[: i + 1]))
        if st.button(part, key=f"crumb_{i}", use_container_width=True):
            st.session_state.current_dir = crumb_path
            st.session_state.idx = 0
            st.session_state.running = False
            st.rerun()

    st.divider()

    # Subfolder list
    try:
        subdirs = sorted(
            d for d in os.listdir(current)
            if os.path.isdir(os.path.join(current, d)) and not d.startswith(".")
        )
    except PermissionError:
        subdirs = []
        st.warning("Permission denied.")

    if subdirs:
        choice = st.selectbox("Subfolders", subdirs, label_visibility="collapsed")
        if st.button("Open ▶", use_container_width=True):
            st.session_state.current_dir = os.path.join(current, choice)
            st.session_state.idx = 0
            st.session_state.running = False
            st.rerun()
    else:
        st.caption("No subfolders")

    st.divider()
    st.header("⚙️ Settings")
    max_size = st.slider("Display width (px)", 100, 2400, 1024, 50)
    display_time = st.slider("Display time (sec)", 1, 10, 2)

    st.divider()
    st.header("▶️ Slideshow")

    images = sorted(
        p for p in Path(current).iterdir()
        if p.suffix.lower() in IMAGE_EXTS
    )
    total = len(images)
    st.caption(f"{total} image(s) in folder")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ Run", use_container_width=True, disabled=total == 0):
            st.session_state.running = True
            st.rerun()
    with col2:
        if st.button("⏹ Stop", use_container_width=True, disabled=not st.session_state.running):
            st.session_state.running = False

# --- Main area ---
st.title("🖼️ Image Directory Slideshow")
st.caption(f"`{current}`")

if total == 0:
    st.info("No images in this folder — navigate to a folder with images.")
else:
    idx = st.session_state.idx % total
    img_path = images[idx]
    image = Image.open(img_path)
    orig_size = image.size
    ratio = max_size / image.width
    image = image.resize((max_size, int(image.height * ratio)), Image.LANCZOS)
    caption = (
        f"{img_path.name}  |  {idx + 1} of {total}  |  "
        f"Original: {orig_size[0]}×{orig_size[1]} px  |  Displayed: {max_size}×{int(orig_size[1] * ratio)} px"
    )
    st.image(image, caption=caption, width=max_size)

    if st.session_state.running:
        time.sleep(display_time)
        st.session_state.idx = (idx + 1) % total
        st.rerun()
