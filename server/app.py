from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import base64, io, os, uuid
from PIL import Image
import numpy as np
import cv2

from recolor import recolor_lab_blend
from pdfgen import build_paint_plan_pdf

app = FastAPI(title="Paint My Room API")

# CORS (open for dev; tighten for prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static
static_dir = os.path.join(os.path.dirname(__file__), "static")
images_dir = os.path.join(static_dir, "images")
pdf_dir = os.path.join(static_dir, "pdf")
os.makedirs(images_dir, exist_ok=True)
os.makedirs(pdf_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

class PdfRequest(BaseModel):
    original_data_url: str
    mask_data_url: str
    wall_hex: str
    trim_hex: Optional[str] = None
    brand: Optional[str] = "SW"

def data_url_to_pil(data_url: str) -> Image.Image:
    # data:image/jpeg;base64,....
    if not data_url.startswith("data:"):
        raise ValueError("Invalid data_url")
    base64_str = data_url.split(",", 1)[1]
    img_bytes = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(img_bytes)).convert("RGB")

def data_url_to_mask(data_url: str, size) -> np.ndarray:
    im = data_url_to_pil(data_url).convert("L").resize(size, Image.NEAREST)
    arr = np.array(im)
    # Any nonzero considered mask
    mask = (arr > 0).astype(np.uint8) * 255
    return mask

def hex_to_bgr(h: str):
    h = h.lstrip("#")
    return (int(h[4:6],16), int(h[2:4],16), int(h[0:2],16))

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/pdf")
def make_pdf(req: PdfRequest):
    try:
        original = data_url_to_pil(req.original_data_url)
        wall_mask = data_url_to_mask(req.mask_data_url, original.size)
        # Recolor server-side in LAB for fidelity
        img_bgr = cv2.cvtColor(np.array(original), cv2.COLOR_RGB2BGR)
        wall_hex = req.wall_hex if req.wall_hex.startswith("#") else ("#"+req.wall_hex)
        recolored_bgr = recolor_lab_blend(img_bgr, wall_mask, hex_to_bgr(wall_hex), luminance_blend=0.9)
        recolored_rgb = cv2.cvtColor(recolored_bgr, cv2.COLOR_BGR2RGB)
        # Save images
        uid = uuid.uuid4().hex[:10]
        img_name = f"recolor_{uid}.jpg"
        img_path = os.path.join(images_dir, img_name)
        Image.fromarray(recolored_rgb).save(img_path, quality=92)
        # Build PDF
        pdf_name = f"paint_plan_{uid}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_name)
        build_paint_plan_pdf(
            pdf_path=pdf_path,
            original=np.array(original),
            preview=recolored_rgb,
            brand=req.brand,
            wall_hex=wall_hex,
            trim_hex=req.trim_hex or "#1E1E1E"
        )
        base = "/static"
        return {
            "preview_url": f"{base}/images/{img_name}",
            "pdf_url": f"{base}/pdf/{pdf_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class Lead(BaseModel):
    email: str
    source: Optional[str] = "widget"
    notes: Optional[str] = None

@app.post("/lead")
def save_lead(lead: Lead):
    # naive CSV append; replace with DB in prod
    import csv
    leads_csv = os.path.join(static_dir, "leads.csv")
    new = not os.path.exists(leads_csv)
    with open(leads_csv, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["email","source","notes"])
        w.writerow([lead.email, lead.source, lead.notes or ""])
    return {"ok": True, "message": "Lead saved."}
