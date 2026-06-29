import streamlit as st
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="YOLO26 Detector", layout="wide")
st.title("**🔍 YOLO26 Object Detection**")
st.caption("**Upload an image, video, or use your webcam to run live inference.**")

# ── Load model (cached so it only loads once) ──────────────────────────────────
@st.cache_resource
def load_model(path: str):
    return YOLO(path)

model = load_model("yolo26l-seg.pt")

# ── Sidebar controls ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("**Settings**")
    confidence = st.slider("**Confidence threshold**", 0.1, 1.0, 0.25, 0.05)
    iou        = st.slider("**NMS IoU threshold**",    0.1, 1.0, 0.5, 0.05)
    source     = st.radio("**Input source**", ["Image", "Video", "Webcam"])
    if source in ("Video", "Webcam"):
        skip = st.slider("**Process every N frames**", 1, 8, 2)

# ── Helper: run model, return annotated frame + label counts + inference ms ────
def detect(frame_bgr: np.ndarray):
    results   = model(frame_bgr, conf=confidence, iou=iou)[0]
    annotated = results.plot()
    inf_ms    = results.speed.get("inference", 0.0)
    counts: dict[str, int] = {}
    if results.boxes is not None and len(results.boxes):
        for idx in results.boxes.cls.cpu().numpy().astype(int):
            name = results.names[idx]
            counts[name] = counts.get(name, 0) + 1
    return annotated, counts, inf_ms

def detections_header(inf_ms: float) -> None:
    st.markdown(
        f"### Detections {'&nbsp;' * 30}"
        f"<span style='font-size:0.5em; font-weight:bold'>inference &nbsp;{inf_ms:.1f} ms</span>",
        unsafe_allow_html=True,
    )

def show_counts(counts: dict[str, int]) -> None:
    if counts:
        text = "  |  ".join(f"{k}: {v}" for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True))
        st.markdown(f"**Detected — {text}**")
    else:
        st.markdown("**No detections.**")

# ── IMAGE ──────────────────────────────────────────────────────────────────────
if source == "Image":
    uploaded = st.file_uploader("**Upload an image**", type=["jpg", "jpeg", "png", "webp"])
    if uploaded:
        img_pil   = Image.open(uploaded).convert("RGB")
        img_bgr   = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        annotated, counts, inf_ms = detect(img_bgr)
        annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("**Original**")
            st.image(img_pil, use_container_width=True)
            st.markdown(f"**{uploaded.name}  |  {img_pil.width} × {img_pil.height} px**")
        with col2:
            detections_header(inf_ms)
            st.image(annotated_rgb, use_container_width=True)
            show_counts(counts)

# ── VIDEO ──────────────────────────────────────────────────────────────────────
elif source == "Video":
    uploaded = st.file_uploader("**Upload a video**", type=["mp4", "mov", "avi", "mkv"])
    if uploaded:
        import tempfile, os

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        cap   = cv2.VideoCapture(tmp_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps   = cap.get(cv2.CAP_PROP_FPS) or 30

        st.info(f"**Video: {total} frames at {fps:.1f} fps — processing every {skip} frame(s).**")
        time_placeholder  = st.empty()
        frame_placeholder = st.empty()
        count_placeholder = st.empty()
        stop = st.button("**⏹ Stop**")

        frame_idx = 0
        while cap.isOpened() and not stop:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % skip == 0:
                annotated, counts, inf_ms = detect(frame)
                with time_placeholder.container():
                    detections_header(inf_ms)
                frame_placeholder.image(
                    cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB),
                    use_container_width=True,
                    caption=f"**Frame {frame_idx}/{total}**"
                )
                with count_placeholder.container():
                    show_counts(counts)
            frame_idx += 1

        cap.release()
        os.unlink(tmp_path)
        st.success("**Done.**")

# ── WEBCAM ─────────────────────────────────────────────────────────────────────
elif source == "Webcam":
    cam_mode = st.radio("**Capture mode**", ["Single Frame", "Continuous Stream"], horizontal=True)

    if cam_mode == "Single Frame":
        img_file = st.camera_input("**Take a photo**")
        if img_file:
            img_pil   = Image.open(img_file).convert("RGB")
            img_bgr   = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            annotated, counts, inf_ms = detect(img_bgr)
            annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("**Original**")
                st.image(img_pil, use_container_width=True)
                st.markdown(f"**Camera capture  |  {img_pil.width} × {img_pil.height} px**")
            with col2:
                detections_header(inf_ms)
                st.image(annotated_rgb, use_container_width=True)
                show_counts(counts)

    else:  # Continuous Stream
        st.caption("**Continuous stream uses the local camera via OpenCV.**")
        run               = st.toggle("**Start stream**")
        time_placeholder  = st.empty()
        frame_placeholder = st.empty()
        count_placeholder = st.empty()

        if run:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                st.error("**Could not open webcam.**")
            else:
                stop      = st.button("**⏹ Stop**")
                frame_idx = 0
                while not stop:
                    ret, frame = cap.read()
                    if not ret:
                        st.warning("**No frame received.**")
                        break
                    if frame_idx % skip == 0:
                        annotated, counts, inf_ms = detect(frame)
                        with time_placeholder.container():
                            detections_header(inf_ms)
                        frame_placeholder.image(
                            cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB),
                            use_container_width=True,
                            channels="RGB",
                        )
                        with count_placeholder.container():
                            show_counts(counts)
                    frame_idx += 1
                cap.release()
