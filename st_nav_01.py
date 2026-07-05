import streamlit as st

st.set_page_config(page_title="YOLO26 App", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 1rem !important; }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1a2e;
        padding: 0.3rem 1rem;
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        color: #e0e0e0;
        font-weight: 600;
        border-radius: 6px;
        padding: 0.4rem 1rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4f8ef7;
        color: white;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #2a2a4e;
        color: white;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"] { display: none; }
</style>
""", unsafe_allow_html=True)

tab_instructions, tab_yolo, tab_new, tab_about = st.tabs(
    ["Instructions", "Yolo26", "New page", "About"]
)

with tab_instructions:
    st.title("Instructions")
    st.markdown("""
    ### Getting Started

    Use the navigation bar above to switch between sections.

    

    ### How to use the Yolo26 model demo:
    1. Select a model size and task in the **Yolo26** tab.
        Select Model task from pull down menu
        - **Object Detection**
        - **Segmentations**
        - **Pose Estimation**
        - **Orientation Estimation** (Try this with streaming or a video and the nano model😎 )
        - **Classification***
    2. Select Model size from pull down menu. 
        - **Nano**  
        - **Small**
        - **Medium**
        - **Large**
        - **Extra Large**   
    The model size will determine accuracy and execution time.
    A suggestion is to use nano (smallest and fastest) or small for stream tests.
    3. Select the image source. Upload an image or video, 
    choose from the provided gallery of test images or use your webcam.
    4. Adjust confidence and IoU thresholds as needed. 
    5. Download annotated results to save your device.
    """)

with tab_yolo:
    st.title("YOLO26 Detection, Pose-Estimation and Segmentation")
    st.info("YOLO26 inference will be wired up here.")
    st.markdown("This tab will host the full YOLO26 demonstrator from `st_yolo_01.py`.")

with tab_new:
    st.title("New Page")
    st.info("This page is a placeholder — add your feature here.")

with tab_about:
    st.title("About")
    st.markdown("""
    **YOLO26 App** — built with [Streamlit](https://streamlit.io).

    - Model: YOLO26 (Ultralytics)
    - UI: Streamlit
    """)
