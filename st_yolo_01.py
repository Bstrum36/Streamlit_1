import streamlit as st
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="YOLO26 Detector", layout="wide")
st.title("🔍 YOLO26 Object Detection")
st.caption("Upload an image, video, or use your webcam to run live inference.")

# ── Load model (cached so it only loads once) ──────────────────────────────────
@st.cache_resource
def load_model(path: str):
    return YOLO(path)

model = load_model("yolo26l-seg.pt")

# ── Sidebar controls ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    confidence = st.slider("Confidence threshold", 0.1, 1.0, 0.4, 0.05)
    iou        = st.slider("NMS IoU threshold",    0.1, 1.0, 0.5, 0.05)
    source     = st.radio("Input source", ["Image", "Video", "Webcam"])

# ── Helper: run model and return annotated frame ───────────────────────────────
def detect(frame_bgr: np.ndarray) -> np.ndarray:
    results = model(frame_bgr, conf=confidence, iou=iou)[0]
    return results.plot()          # returns BGR numpy array with boxes drawn

# ── IMAGE ──────────────────────────────────────────────────────────────────────
if source == "Image":
    uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "webp"])
    if uploaded:
        img_pil   = Image.open(uploaded).convert("RGB")
        img_bgr   = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        annotated = detect(img_bgr)
        annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Original")
            st.image(img_pil, use_container_width=True)
        with col2:
            st.subheader("Detections")
            st.image(annotated_rgb, use_container_width=True)

# ── VIDEO ──────────────────────────────────────────────────────────────────────
elif source == "Video":
    uploaded = st.file_uploader("Upload a video", type=["mp4", "mov", "avi", "mkv"])
    if uploaded:
        import tempfile, os

        # Write to a temp file so OpenCV can open it
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        cap        = cv2.VideoCapture(tmp_path)
        total      = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps        = cap.get(cv2.CAP_PROP_FPS) or 30
        skip       = st.sidebar.slider("Process every N frames", 1, 8, 2)

        st.info(f"Video: {total} frames at {fps:.1f} fps — processing every {skip} frame(s).")
        frame_placeholder = st.empty()
        stop = st.button("⏹ Stop")

        frame_idx = 0
        while cap.isOpened() and not stop:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % skip == 0:
                annotated = detect(frame)
                frame_placeholder.image(
                    cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB),
                    use_container_width=True,
                    caption=f"Frame {frame_idx}/{total}"
                )
            frame_idx += 1

        cap.release()
        os.unlink(tmp_path)
        st.success("Done.")

# ── WEBCAM ─────────────────────────────────────────────────────────────────────
elif source == "Webcam":
    st.info("Webcam capture runs locally — make sure your browser grants camera access.")
    run  = st.toggle("Start webcam")
    placeholder = st.empty()

    if run:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("Could not open webcam. Check that no other app is using it.")
        else:
            stop = st.button("⏹ Stop webcam")
            while not stop:
                ret, frame = cap.read()
                if not ret:
                    st.warning("No frame received.")
                    break
                annotated = detect(frame)
                placeholder.image(
                    cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB),
                    use_container_width=True,
                    channels="RGB"
                )
            cap.release()