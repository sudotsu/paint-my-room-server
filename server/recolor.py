import cv2
import numpy as np

def recolor_lab_blend(img_bgr: np.ndarray, mask: np.ndarray, target_bgr, luminance_blend=0.9):
    # Recolor the masked region by blending a/b channels toward target color in Lab space.
    # Keeps L (lightness) mostly intact to preserve shadows and texture.
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    L, A, B = cv2.split(lab)
    target_lab = cv2.cvtColor(
        np.uint8([[list(target_bgr)]]), cv2.COLOR_BGR2LAB
    ).astype(np.float32)[0,0]

    # Normalize mask to 0..1 with gentle feather for softer edges
    m = (cv2.GaussianBlur(mask, (0,0), 1.2) / 255.0).astype(np.float32)

    # a/b toward target; keep L unchanged for strongest shadow retention
    A = A*(1-m) + (A*(1-luminance_blend) + target_lab[1]*luminance_blend)*m
    B = B*(1-m) + (B*(1-luminance_blend) + target_lab[2]*luminance_blend)*m

    out_lab = cv2.merge([L, A, B]).astype(np.uint8)
    return cv2.cvtColor(out_lab, cv2.COLOR_LAB2BGR)
