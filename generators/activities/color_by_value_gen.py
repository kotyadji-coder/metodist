"""Generate color-by-value outline from a flat-color image.

Pipeline:
1. Take a flat-color image (few colors, no gradients)
2. Quantize to exact N colors
3. Draw black borders where adjacent pixels differ in color
4. Find connected regions, number them
5. Output: outline PNG + legend mapping
"""

from collections import deque
from io import BytesIO

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _quantize(img: Image.Image, n_colors: int) -> np.ndarray:
    """Quantize image to n_colors, return numpy RGB array."""
    img = img.convert("RGB")
    q = img.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT)
    return np.array(q.convert("RGB"))


def _find_regions(arr: np.ndarray, min_area: int) -> list[dict]:
    """Find connected regions via flood fill. Returns list of {color, mask, centroid, area}."""
    h, w = arr.shape[:2]
    visited = np.zeros((h, w), dtype=bool)
    regions = []

    for y in range(h):
        for x in range(w):
            if visited[y, x]:
                continue
            color = tuple(arr[y, x])
            mask = np.zeros((h, w), dtype=bool)
            queue = deque([(y, x)])
            visited[y, x] = True
            mask[y, x] = True
            px_sum_x, px_sum_y, count = 0, 0, 0

            while queue:
                cy, cx = queue.popleft()
                px_sum_x += cx
                px_sum_y += cy
                count += 1
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                        if tuple(arr[ny, nx]) == color:
                            visited[ny, nx] = True
                            mask[ny, nx] = True
                            queue.append((ny, nx))

            if count >= min_area:
                regions.append({
                    "color": color,
                    "mask": mask,
                    "centroid": (px_sum_x / count, px_sum_y / count),
                    "area": count,
                })

    return regions


def _color_name(color: tuple) -> str:
    """Map RGB to Russian color name."""
    r, g, b = color
    # Convert to HSV for better detection
    hsv = cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_RGB2HSV)[0][0]
    h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])

    if v < 50:
        return "чёрный"
    if s < 30 and v > 200:
        return "белый"
    if s < 40:
        return "серый"

    # By hue
    if h < 10 or h > 170:
        return "красный"
    if h < 22:
        return "оранжевый"
    if h < 35:
        return "жёлтый"
    if h < 80:
        return "зелёный"
    if h < 100:
        return "голубой"
    if h < 130:
        return "синий"
    if h < 155:
        return "фиолетовый"
    return "розовый"


def _rgb_to_hex(c: tuple) -> str:
    return f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"


def image_to_color_by_value(
    image_bytes: bytes,
    n_colors: int = 5,
    target_w: int = 400,
) -> dict:
    """Convert flat-color image to color-by-value outline.

    Returns:
        {
            "outline_png": bytes (PNG of white image with black borders and zone numbers),
            "colored_png": bytes (PNG of colored version for answer key),
            "legend": {color_name: {"hex": str, "zones": [int]}},
            "zone_count": int,
        }
    """
    # Load and resize
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    aspect = img.height / img.width
    target_h = int(target_w * aspect)
    img = img.resize((target_w, target_h), Image.LANCZOS)

    # Quantize
    arr = _quantize(img, n_colors)
    h, w = arr.shape[:2]

    # Find regions
    regions = _find_regions(arr, min_area=int(w * h * 0.005))

    # Sort by area descending so big regions get low numbers
    regions.sort(key=lambda r: -r["area"])

    # === Build OUTLINE image ===
    outline = np.full((h, w, 3), 255, dtype=np.uint8)  # white

    # Draw borders: where adjacent pixels have different colors
    for y in range(h):
        for x in range(w):
            for dy, dx in [(0, 1), (1, 0)]:
                ny, nx = y + dy, x + dx
                if ny < h and nx < w:
                    if not np.array_equal(arr[y, x], arr[ny, nx]):
                        outline[y, x] = [0, 0, 0]
                        outline[ny, nx] = [0, 0, 0]

    # Thicken borders
    kernel = np.ones((2, 2), np.uint8)
    border_mask = (outline[:, :, 0] == 0).astype(np.uint8) * 255
    border_mask = cv2.dilate(border_mask, kernel, iterations=1)
    outline[border_mask > 0] = [0, 0, 0]

    # === Build COLORED image (answer key) ===
    colored = arr.copy()
    colored[border_mask > 0] = [0, 0, 0]

    # === Add zone numbers ===
    outline_pil = Image.fromarray(outline)
    colored_pil = Image.fromarray(colored)
    draw_outline = ImageDraw.Draw(outline_pil)
    draw_colored = ImageDraw.Draw(colored_pil)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=14)
    except Exception:
        font = ImageFont.load_default()

    legend: dict[str, dict] = {}

    for i, region in enumerate(regions):
        num = i + 1
        cx, cy = region["centroid"]
        cx, cy = int(cx), int(cy)

        # Draw number
        text = str(num)
        bbox = draw_outline.textbbox((cx, cy), text, font=font, anchor="mm")
        # White background for readability
        pad = 2
        draw_outline.rectangle([bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad], fill="white")
        draw_outline.text((cx, cy), text, fill="black", font=font, anchor="mm")

        draw_colored.rectangle([bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad], fill="white")
        draw_colored.text((cx, cy), text, fill="black", font=font, anchor="mm")

        # Legend
        cname = _color_name(region["color"])
        if cname not in legend:
            legend[cname] = {"hex": _rgb_to_hex(region["color"]), "zones": []}
        legend[cname]["zones"].append(num)

    # Export PNGs
    buf_outline = BytesIO()
    outline_pil.save(buf_outline, format="PNG")

    buf_colored = BytesIO()
    colored_pil.save(buf_colored, format="PNG")

    return {
        "outline_png": buf_outline.getvalue(),
        "colored_png": buf_colored.getvalue(),
        "legend": legend,
        "zone_count": len(regions),
    }
