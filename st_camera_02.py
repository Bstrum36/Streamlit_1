import time
from io import BytesIO

import streamlit as st
from PIL import Image

IMAGE_EXTS = ["jpg", "jpeg", "png", "bmp", "webp"]

for key, val in [("running", False), ("idx", 0), ("file_data", [])]:
    if key not in st.session_state:
        st.session_state[key] = val

# --- Sidebar ---
with st.sidebar:
    st.header("📁 Upload Images")
    uploaded = st.file_uploader(
        "Open a folder, press Ctrl+A to select all, then click Open",
        type=IMAGE_EXTS,
        accept_multiple_files="directory",
        label_visibility="visible",
    )

    # Load file bytes into session state whenever the selection changes
    if uploaded is not None:
        names = [f.name for f in uploaded]
        stored = [d["name"] for d in st.session_state.file_data]
        if names != stored:
            st.session_state.file_data = [
                {"name": f.name, "data": f.read()} for f in uploaded
            ]
            st.session_state.idx = 0
            st.session_state.running = False

    total = len(st.session_state.file_data)

    st.divider()
    st.header("⚙️ Settings")
    max_size = st.slider("Display width (px)", 100, 2400, 1024, 50)
    display_time = st.slider("Display time (sec)", 1, 10, 2)

    st.divider()
    st.header("▶️ Slideshow")
    st.caption(f"{total} image(s) loaded")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ Run", use_container_width=True, disabled=total == 0):
            st.session_state.running = True
            st.session_state.idx = 0
            st.rerun()
    with col2:
        if st.button("⏹ Stop", use_container_width=True, disabled=not st.session_state.running):
            st.session_state.running = False

# --- Main area ---
st.title("🖼️ Image Slideshow")

total = len(st.session_state.file_data)

if total == 0:
    st.info("Use the sidebar uploader to select images. Navigate to your folder and press Ctrl+A to select all images at once.")
else:
    idx = st.session_state.idx % total
    entry = st.session_state.file_data[idx]
    image = Image.open(BytesIO(entry["data"]))
    orig_size = image.size
    ratio = max_size / image.width
    image = image.resize((max_size, int(image.height * ratio)), Image.LANCZOS)
    caption = (
        f"{entry['name']}  |  {idx + 1} of {total}  |  "
        f"Original: {orig_size[0]}×{orig_size[1]} px  |  Displayed: {max_size}×{int(orig_size[1] * ratio)} px"
    )
    st.image(image, caption=caption, width=max_size)

    if st.session_state.running:
        time.sleep(display_time)
        st.session_state.idx = (idx + 1) % total
        st.rerun()
