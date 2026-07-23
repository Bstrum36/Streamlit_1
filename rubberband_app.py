"""
Rubber-Band Selection Box in Streamlit
---------------------------------------
Upload an image; a transparent drawing canvas is overlaid on top.
Drag to draw a box.  Drag the box body to move it.
Drag any of the 8 handles to resize.
Corner coordinates are displayed below the canvas.

Run with:
    streamlit run rubberband_app.py
"""

import io
import base64
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

MAX_W, MAX_H = 1280, 1024

st.set_page_config(page_title="Rubber-Band Box", layout="wide")
st.title("Rubber-Band Selection Box")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Options")
    uploaded_file = st.file_uploader("Load image", type=["png", "jpg", "jpeg"])
    st.divider()
    stroke_color = st.color_picker("Box colour", "#FF4B4B")
    stroke_width = st.slider("Border width", 1, 10, 2)
    fill_opacity = st.slider("Fill opacity", 0.0, 0.5, 0.1, 0.05)

if uploaded_file is None:
    st.info("Upload an image using the sidebar to get started.")
    st.stop()

# ── Load & proportionally fit image ───────────────────────────────────────────
raw = Image.open(uploaded_file).convert("RGB")
ow, oh = raw.size
scale    = min(MAX_W / ow, MAX_H / oh, 1.0)      # never upscale
canvas_w = max(1, int(ow * scale))
canvas_h = max(1, int(oh * scale))
img      = raw.resize((canvas_w, canvas_h), Image.LANCZOS)

size_kb = uploaded_file.size / 1024
file_size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
dims = (f"{ow}×{oh} px  →  {canvas_w}×{canvas_h} px" if scale < 1.0
        else f"{ow}×{oh} px")
st.markdown(
    f"<span style='color:white; font-weight:bold; font-size:1rem;'>"
    f"{uploaded_file.name} &nbsp;|&nbsp; {file_size_str} &nbsp;|&nbsp; {dims}"
    f"</span>",
    unsafe_allow_html=True,
)

# ── Encode image as base64 ─────────────────────────────────────────────────────
buf = io.BytesIO()
img.save(buf, format="JPEG", quality=88)
b64 = base64.b64encode(buf.getvalue()).decode()

# ── Build self-contained HTML component ───────────────────────────────────────
INFO_H = 96   # height of the coordinates bar below canvas

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; overflow: hidden; }}
  .wrap {{ position: relative; display: block; width: {canvas_w}px; height: {canvas_h}px; line-height: 0; }}
  .wrap img {{ display: block; width: {canvas_w}px; height: {canvas_h}px; user-select: none; }}
  .wrap canvas {{ position: absolute; top: 0; left: 0; cursor: crosshair; }}
  .info {{
    width: {canvas_w}px; height: {INFO_H}px;
    background: #1a1a2e; color: #e0e0e0;
    font: 13px/1 monospace; padding: 8px 12px;
    display: flex; align-items: center; gap: 20px; flex-wrap: wrap;
  }}
  .info b {{ color: #4f8ef7; }}
</style>
</head>
<body>
<div class="wrap">
  <img src="data:image/jpeg;base64,{b64}" draggable="false" />
  <canvas id="c" width="{canvas_w}" height="{canvas_h}"></canvas>
</div>
<div class="info" id="info">Draw a rectangle on the image above.</div>

<script>
const canvas = document.getElementById('c');
const ctx    = canvas.getContext('2d');
const info   = document.getElementById('info');

const STROKE_COLOR = '{stroke_color}';
const LINE_W       = {stroke_width};
const FILL_A       = {fill_opacity};
const HR           = 7;   // handle hit radius (px)

let box      = null;   // always in normalised form {{x,y,w,h}}
let rawBox   = null;   // while drawing (may have negative w/h)
let interactMode = 'idle';   // 'idle' | 'draw' | 'move' | 'resize'
let activeHandle = -1;
let drag0    = null;   // {{mx,my, box snapshot}}

// ── Helpers ─────────────────────────────────────────────────────────────────
function norm(b) {{
  return {{
    x: b.w >= 0 ? b.x : b.x + b.w,
    y: b.h >= 0 ? b.y : b.y + b.h,
    w: Math.abs(b.w),
    h: Math.abs(b.h)
  }};
}}

function handles(b) {{
  const {{x,y,w,h}} = b;
  return [
    {{x,           y,           c:'nw-resize'}},
    {{x: x+w/2,    y,           c:'n-resize' }},
    {{x: x+w,      y,           c:'ne-resize'}},
    {{x: x+w,      y: y+h/2,    c:'e-resize' }},
    {{x: x+w,      y: y+h,      c:'se-resize'}},
    {{x: x+w/2,    y: y+h,      c:'s-resize' }},
    {{x,           y: y+h,      c:'sw-resize'}},
    {{x,           y: y+h/2,    c:'w-resize' }},
  ];
}}

function hitHandle(b, mx, my) {{
  return handles(b).findIndex(h => (mx-h.x)**2 + (my-h.y)**2 <= (HR+2)**2);
}}

function insideBox(b, mx, my) {{
  return mx >= b.x && mx <= b.x+b.w && my >= b.y && my <= b.y+b.h;
}}

// ── Render ───────────────────────────────────────────────────────────────────
function render(showHandles) {{
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const b = box;
  if (!b) return;

  ctx.fillStyle   = `rgba(255,165,0,${{FILL_A}})`;
  ctx.fillRect(b.x, b.y, b.w, b.h);
  ctx.strokeStyle = STROKE_COLOR;
  ctx.lineWidth   = LINE_W;
  ctx.strokeRect(b.x, b.y, b.w, b.h);

  if (showHandles) {{
    handles(b).forEach(h => {{
      ctx.beginPath();
      ctx.arc(h.x, h.y, HR, 0, Math.PI*2);
      ctx.fillStyle   = '#ffffff';
      ctx.fill();
      ctx.strokeStyle = STROKE_COLOR;
      ctx.lineWidth   = 1.5;
      ctx.stroke();
    }});
  }}

  const x1=Math.round(b.x), y1=Math.round(b.y);
  const x2=Math.round(b.x+b.w), y2=Math.round(b.y+b.h);
  info.innerHTML =
    `<b>TL</b> (${{x1}}, ${{y1}}) &nbsp;` +
    `<b>TR</b> (${{x2}}, ${{y1}}) &nbsp;` +
    `<b>BL</b> (${{x1}}, ${{y2}}) &nbsp;` +
    `<b>BR</b> (${{x2}}, ${{y2}}) &nbsp;&nbsp;` +
    `<b>W×H</b> ${{Math.round(b.w)}}×${{Math.round(b.h)}}`;
}}

// ── Event: mousedown ─────────────────────────────────────────────────────────
canvas.addEventListener('mousedown', e => {{
  e.preventDefault();
  const r  = canvas.getBoundingClientRect();
  const mx = e.clientX - r.left, my = e.clientY - r.top;

  if (box) {{
    const h = hitHandle(box, mx, my);
    if (h >= 0) {{
      interactMode = 'resize';
      activeHandle = h;
      drag0 = {{mx, my, box: {{...box}}}};
      return;
    }}
    if (insideBox(box, mx, my)) {{
      interactMode = 'move';
      drag0 = {{mx, my, box: {{...box}}}};
      return;
    }}
  }}
  // Start a new box
  interactMode = 'draw';
  rawBox = {{x: mx, y: my, w: 0, h: 0}};
  box    = norm(rawBox);
  drag0  = {{mx, my}};
}});

// ── Event: mousemove ─────────────────────────────────────────────────────────
canvas.addEventListener('mousemove', e => {{
  const r  = canvas.getBoundingClientRect();
  const mx = e.clientX - r.left, my = e.clientY - r.top;

  if (!drag0) {{
    // Hover cursor
    if (box) {{
      const h = hitHandle(box, mx, my);
      canvas.style.cursor = h >= 0 ? handles(box)[h].c
                          : insideBox(box, mx, my) ? 'move'
                          : 'crosshair';
    }}
    return;
  }}

  const dx = mx - drag0.mx, dy = my - drag0.my;
  const ob = drag0.box;

  if (interactMode === 'draw') {{
    rawBox.w = mx - rawBox.x;
    rawBox.h = my - rawBox.y;
    box = norm(rawBox);
    render(false);

  }} else if (interactMode === 'move') {{
    box = {{x: ob.x+dx, y: ob.y+dy, w: ob.w, h: ob.h}};
    render(true);

  }} else if (interactMode === 'resize') {{
    let {{x,y,w,h}} = ob;
    if      (activeHandle===0) {{ x+=dx; y+=dy; w-=dx; h-=dy; }}
    else if (activeHandle===1) {{ y+=dy; h-=dy; }}
    else if (activeHandle===2) {{ y+=dy; w+=dx; h-=dy; }}
    else if (activeHandle===3) {{ w+=dx; }}
    else if (activeHandle===4) {{ w+=dx; h+=dy; }}
    else if (activeHandle===5) {{ h+=dy; }}
    else if (activeHandle===6) {{ x+=dx; w-=dx; h+=dy; }}
    else if (activeHandle===7) {{ x+=dx; w-=dx; }}
    box = norm({{x,y,w,h}});
    render(true);
  }}
}});

// ── Event: mouseup ───────────────────────────────────────────────────────────
canvas.addEventListener('mouseup', () => {{
  drag0 = null;
  interactMode = 'idle';
  render(true);
}});

canvas.addEventListener('mouseleave', () => {{
  if (interactMode === 'draw') {{ drag0 = null; interactMode = 'idle'; render(true); }}
}});
</script>
</body>
</html>"""

components.html(html, height=canvas_h + INFO_H + 4, scrolling=False)
