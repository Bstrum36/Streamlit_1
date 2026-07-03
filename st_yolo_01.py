import streamlit as st
import cv2
import numpy as np
import tempfile
import os
import threading
from io import BytesIO
from PIL import Image
from ultralytics import YOLO
from pathlib import Path
import av
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase


def model_maker(msize, mtask):
    """
    Build a YOLO26 model name string from a size code and a task name.

    Parameters
    ----------
    msize : str
        Single character model size. Valid (case-insensitive): n, s, m, l, x.
    mtask : str
        Task name. Valid: "Detection", "Instance Segmentation",
        "Semantic Segmentation", "Pose-Estimation", "Orientation Detection",
        "Classification".

    Returns
    -------
    str
        Model name, e.g. "yolo26n", "yolo26s-seg", "yolo26x-pose".
    """
    # --- validate size ---
    if not isinstance(msize, str) or len(msize) != 1:
        raise ValueError("msize must be a single character string.")

    msize = msize.lower()
    valid_sizes = {"n", "s", "m", "l", "x"}
    if msize not in valid_sizes:
        raise ValueError(f"msize must be one of {sorted(valid_sizes)}, got '{msize}'.")

    # --- validate task ---
    if not isinstance(mtask, str):
        raise ValueError("mtask must be a string.")

    # Map task -> YOLO suffix
    # Note: YOLO doesn't natively distinguish "semantic" vs "instance"
    # segmentation (it only ships instance segmentation, "-seg"), so both
    # are mapped to "-seg" here as a reasonable assumption.
    task_map = {
        "detection": "",
        "instance segmentation": "-seg",
        "semantic segmentation": "-seg",
        "pose-estimation": "-pose",
        "orientation detection": "-obb",
        "classification": "-cls",
    }

    key = mtask.strip().lower()
    if key not in task_map:
        raise ValueError(
            f"mtask must be one of {list(task_map.keys())} (case-insensitive), got '{mtask}'."
        )

    suffix = task_map[key]

    return f"yolo26{msize}{suffix}"

IMAGES_DIR = Path("Images")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="YOLO26 Demonstrator", layout="wide")
st.title("**🔍 YOLO26 Detection, Segmentation and Pose Estimation**")
st.caption("**Upload an image, video, or use your webcam to run live inference.**")
st.markdown("""
<style>
button[data-testid="stBaseButton-secondary"] {
    background-color: #e8e8e8 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Load model (cached so it only loads once) ──────────────────────────────────
@st.cache_resource
def load_model(path: str):
    return YOLO(path)

# ── Sidebar controls ───────────────────────────────────────────────────────────
if "show_model_picker" not in st.session_state:
    st.session_state.show_model_picker = False

# Initialize model selection defaults
if "sel_task" not in st.session_state:
    st.session_state.sel_task = "Instance Segmentation"
if "sel_size" not in st.session_state:
    st.session_state.sel_size = "Large"

with st.sidebar:
    st.header("**Settings**")
    if st.button(":blue[**Select Model**]"):
        st.session_state.show_model_picker = not st.session_state.show_model_picker
    
    if st.session_state.show_model_picker:
        st.selectbox("**Function**", [
            "Detection",
            "Instance Segmentation",
            "Semantic Segmentation",
            "Pose-Estimation",
            "Orientation Detection",
            "Classification",
        ], key="sel_task")
        
        st.selectbox("**Model Size**", [
            "Nano", "Small", "Medium", "Large", "Xtra Large",
        ], key="sel_size")
    
    st.divider()
    confidence = st.slider("**Confidence threshold**", 0.1, 1.0, 0.25, 0.05)
    iou        = st.slider("**NMS IoU threshold**",    0.1, 1.0, 0.5, 0.05)
    
    st.divider()
    source = st.radio("**Input source**", ["Upload an Image", "Sample Images", "Video", "Webcam"])
    
    # Unified input picker
    input_file = None
    if source == "Upload an Image":
        input_file = st.file_uploader("**Upload an image**", type=["jpg", "jpeg", "png", "webp"])
    elif source == "Sample Images":
        exts  = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        if IMAGES_DIR.exists():
            files = sorted([f for f in IMAGES_DIR.iterdir() if f.suffix.lower() in exts])
            if files:
                input_file = st.selectbox("**Select a sample image**", files, format_func=lambda x: x.name, index=None, placeholder="Choose an image…")
            else:
                st.warning(f"**No images found in {IMAGES_DIR}/**")
        else:
            st.error(f"**Directory {IMAGES_DIR}/ not found.**")
    elif source == "Video":
        input_file = st.file_uploader("**Upload a video**", type=["mp4", "mov", "avi", "mkv"])

    if source == "Webcam":
        cam_mode = st.radio("**Webcam mode**", ["Single Frame", "Continuous Stream"])
    else:
        cam_mode = "Single Frame"

    if source in ("Video", "Webcam"):
        skip = st.slider("**Process every N frames**", 1, 8, 2)

# --- Create model using model_maker and sidebar results ---
size_map = {"Nano": "n", "Small": "s", "Medium": "m", "Large": "l", "Xtra Large": "x"}
m_size_code = size_map.get(st.session_state.sel_size, "l")
model_name = model_maker(m_size_code, st.session_state.sel_task)
model = load_model(f"{model_name}.pt")

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
        f"<span style='font-size:0.85em; font-weight:bold'>inference &nbsp;{inf_ms:.1f} ms</span>",
        unsafe_allow_html=True,
    )

def show_counts(counts: dict[str, int]) -> None:
    if counts:
        text = "  |  ".join(f"{k}: {v}" for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True))
        st.markdown(f"**Detected — {text}**")
    else:
        st.markdown("**No detections.**")

class YOLOProcessor(VideoProcessorBase):
    def __init__(self):
        self.confidence = 0.25
        self.iou = 0.5
        self.skip = 2
        self._lock = threading.Lock()
        self.last_counts: dict = {}
        self.last_inf_ms: float = 0.0
        self._frame_idx = 0
        self._last_annotated = None

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        self._frame_idx += 1
        if self._frame_idx % self.skip == 0:
            results = model(img, conf=self.confidence, iou=self.iou)[0]
            annotated = results.plot()
            counts: dict = {}
            if results.boxes is not None and len(results.boxes):
                for idx in results.boxes.cls.cpu().numpy().astype(int):
                    name = results.names[idx]
                    counts[name] = counts.get(name, 0) + 1
            with self._lock:
                self.last_counts = counts
                self.last_inf_ms = results.speed.get("inference", 0.0)
                self._last_annotated = annotated
        annotated = self._last_annotated if self._last_annotated is not None else img
        return av.VideoFrame.from_ndarray(annotated, format="bgr24")

# ── IMAGE / SAMPLE ─────────────────────────────────────────────────────────────
if source in ("Upload an Image", "Sample Images"):
    if input_file:
        img_pil   = Image.open(input_file).convert("RGB")
        img_bgr   = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        annotated, counts, inf_ms = detect(img_bgr)
        annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

        st.caption(f"**Model: `{model_name}` &nbsp;|&nbsp; Task: {st.session_state.sel_task} &nbsp;|&nbsp; Size: {st.session_state.sel_size}**")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("**Original**")
            st.image(img_pil, use_container_width=True)
            st.markdown(f"**{input_file.name}  |  {img_pil.width} × {img_pil.height} px**")
        with col2:
            detections_header(inf_ms)
            st.image(annotated_rgb, use_container_width=True)
            show_counts(counts)
            if isinstance(input_file, Path):
                orig_ext = input_file.suffix.lower()
                dl_name = f"{input_file.stem}_detected{orig_ext}"
            else:
                orig_ext = Path(input_file.name).suffix.lower() or ".png"
                dl_name = f"{Path(input_file.name).stem}_detected{orig_ext}"
            fmt = orig_ext.lstrip(".").upper()
            fmt = "JPEG" if fmt in ("JPG", "JPEG") else fmt
            buf = BytesIO()
            Image.fromarray(annotated_rgb).save(buf, format=fmt)
            st.download_button(":blue[**Download**]", data=buf.getvalue(),
                               file_name=dl_name, mime=f"image/{orig_ext.lstrip('.')}",
                               key="dl_btn_img")
    else:
        st.info("**Please select or upload an image in the sidebar.**")

# ── VIDEO ──────────────────────────────────────────────────────────────────────
elif source == "Video":
    if input_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(input_file.read())
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
    else:
        st.info("**Please upload a video.**")

# ── WEBCAM ─────────────────────────────────────────────────────────────────────
elif source == "Webcam":
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
                buf = BytesIO()
                Image.fromarray(annotated_rgb).save(buf, format="PNG")
                st.download_button(":blue[**Download**]", data=buf.getvalue(),
                                   file_name="capture_detected.png", mime="image/png",
                                   key="dl_btn_cam")

    else:  # Continuous Stream
        ctx = webrtc_streamer(
            key="yolo-webrtc",
            video_processor_factory=YOLOProcessor,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={"video": True, "audio": False},
        )
        if ctx.video_processor:
            ctx.video_processor.confidence = confidence
            ctx.video_processor.iou = iou
            ctx.video_processor.skip = skip
            with ctx.video_processor._lock:
                counts = ctx.video_processor.last_counts.copy()
                inf_ms = ctx.video_processor.last_inf_ms
            detections_header(inf_ms)
            show_counts(counts)
