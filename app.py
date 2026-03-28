from flask import Flask, request, render_template, send_file
from PIL import Image, ImageOps, ImageEnhance
from io import BytesIO
from dotenv import load_dotenv
import requests
import cloudinary
import cloudinary.uploader
import cloudinary.utils
import os
import rembg

load_dotenv()

app = Flask(__name__)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# ---- Startup key validation (Cloudinary only now) ----
_MISSING_KEYS = [k for k in [
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"
] if not os.getenv(k)]
if _MISSING_KEYS:
    print("\n" + "="*60)
    print("WARNING: Cloudinary API keys are missing.")
    print("Background removal will still work (using local AI).")
    print("However, AI photo enhancement will be skipped.")
    print("="*60 + "\n")


@app.route("/")
def index():
    return render_template("index.html")


# Map color name to RGB tuple
BG_COLOR_MAP = {
    "white":  (255, 255, 255),
    "blank":  (255, 255, 255),  # blank = white paper (bg already removed)
    "red":    (220, 50,  50),
    "blue":   (0,   90,  180),
    "yellow": (255, 213, 0),
    "green":  (34,  139, 57),
    "orange": (255, 140, 0),
    "pink":   (255, 105, 180),
    "darkviolet": (148, 0, 211),
}

# Paper sizes in pixels at 300 DPI (width x height)
PAPER_SIZES = {
    "a4":     (2480, 3508),
    "letter": (2550, 3300),
    "4x6":    (1800, 1200),
}


def process_single_image(input_image_bytes, bg_color="white"):
    """Remove background, enhance, and return a ready-to-paste passport PIL image."""
    fill_rgb = BG_COLOR_MAP.get(bg_color, (255, 255, 255))

    # Step 1: Background removal using local rembg
    try:
        input_img = Image.open(BytesIO(input_image_bytes))
        bg_removed_img = rembg.remove(input_img)
    except Exception as e:
        print("rembg error:", e)
        raise ValueError("bg_removal_failed:local_rembg_error")

    if bg_removed_img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", bg_removed_img.size, fill_rgb)
        background.paste(bg_removed_img, mask=bg_removed_img.split()[-1])
        processed_img = background
    else:
        processed_img = bg_removed_img.convert("RGB")

    # If Cloudinary keys are missing, skip enhancement and do basic local sharpening
    if _MISSING_KEYS:
        print("DEBUG: Skipping Cloudinary, applying local sharpening fallback")
        enhancer = ImageEnhance.Sharpness(processed_img)
        return enhancer.enhance(1.5)  # slight sharpen

    # Step 2: Upload to Cloudinary (if keys exist)
    buffer = BytesIO()
    processed_img.save(buffer, format="PNG")
    buffer.seek(0)
    upload_result = cloudinary.uploader.upload(buffer, resource_type="image")
    image_url = upload_result.get("secure_url")
    public_id = upload_result.get("public_id")

    if not image_url:
        raise ValueError("cloudinary_upload_failed")

    # Step 3: Enhance via Cloudinary AI
    enhanced_url = cloudinary.utils.cloudinary_url(
        public_id,
        transformation=[
            {"effect": "gen_restore"},
            {"quality": "auto"},
            {"fetch_format": "auto"},
        ],
    )[0]

    enhanced_img_data = requests.get(enhanced_url).content
    img = Image.open(BytesIO(enhanced_img_data))

    if img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", img.size, fill_rgb)
        background.paste(img, mask=img.split()[-1])
        passport_img = background
    else:
        passport_img = img.convert("RGB")

    return passport_img


def scale_paper_size(base_w, base_h, dpi):
    """Scale paper dimensions from 300 DPI base to target DPI."""
    factor = dpi / 300.0
    return int(base_w * factor), int(base_h * factor)


def layout_mixed_flow(photos_list, page_w, page_h, gap, margin_x, margin_y, photos_per_page):
    """Flow layout that natively supports mixing Landscape and Portrait images smoothly on the same page."""
    pages = []
    current_page = Image.new("RGB", (page_w, page_h), "white")
    x, y = margin_x, margin_y
    row_max_h = 0
    count_on_page = 0

    def new_page():
        nonlocal current_page, x, y, row_max_h, count_on_page
        pages.append(current_page)
        current_page = Image.new("RGB", (page_w, page_h), "white")
        x, y = margin_x, margin_y
        row_max_h = 0
        count_on_page = 0

    for pimg in photos_list:
        w, h = pimg.size

        # Force new page if count limit reached
        if photos_per_page and count_on_page >= photos_per_page:
            new_page()

        # Wrap to next row
        if x + w > page_w - margin_x:
            if x != margin_x:  # Only if row is not empty
                x = margin_x
                y += row_max_h + gap
                row_max_h = 0

        # Run out of vertical space -> new page
        if y + h > page_h - margin_y:
            new_page()

        # Place image
        current_page.paste(pimg, (x, y))
        x += w + gap
        row_max_h = max(row_max_h, h)
        count_on_page += 1

    pages.append(current_page)
    return pages


@app.route("/process", methods=["POST"])
def process():
    print("==== /process endpoint hit ====")

    # Keys guard condition - no longer needed as missing cloudinary falls back to local processing
    # if _MISSING_KEYS:
    #     pass

    # Layout / appearance settings
    passport_width  = int(request.form.get("width", 390))
    passport_height = int(request.form.get("height", 480))
    border   = int(request.form.get("border", 2))
    spacing  = int(request.form.get("spacing", 10))
    orientation = request.form.get("orientation", "horizontal")   # 'horizontal' | 'vertical' | 'both'
    bg_color    = request.form.get("bg_color", "white")
    dpi         = int(request.form.get("dpi", 300))
    paper_size  = request.form.get("paper_size", "a4").lower()
    photos_per_page_raw = request.form.get("photos_per_page", "")
    photos_per_page = int(photos_per_page_raw) if photos_per_page_raw.strip().isdigit() and int(photos_per_page_raw) > 0 else None

    rows_per_col = 5
    margin_x = 10
    margin_y = 10
    gap = spacing

    # Paper size
    base_w, base_h = PAPER_SIZES.get(paper_size, PAPER_SIZES["a4"])
    a4_w, a4_h = scale_paper_size(base_w, base_h, dpi)

    # Collect images, their copy counts, and per-photo orientation
    images_data = []
    i = 0
    while f"image_{i}" in request.files:
        file = request.files[f"image_{i}"]
        copies = int(request.form.get(f"copies_{i}", 6))
        photo_orient = request.form.get(f"orientation_{i}", orientation)  # fallback to global
        images_data.append((file.read(), copies, photo_orient))
        i += 1

    # Fallback to single image mode
    if not images_data and "image" in request.files:
        file = request.files["image"]
        copies = int(request.form.get("copies", 6))
        images_data.append((file.read(), copies, orientation))

    if not images_data:
        return "No image uploaded", 400

    print(f"DEBUG: Processing {len(images_data)} image(s), global orientation={orientation}, bg_color={bg_color}, dpi={dpi}, paper={paper_size}")

    # Process all images
    all_photos = []
    for idx, (img_bytes, copies, photo_orient) in enumerate(images_data):
        print(f"DEBUG: Processing image {idx + 1}, copies={copies}, orient={photo_orient}")
        try:
            img = process_single_image(img_bytes, bg_color=bg_color)
            img = img.resize((passport_width, passport_height), Image.LANCZOS)
            img = ImageOps.expand(img, border=border, fill="black")

            # Rotate if horizontal (landscape)
            if photo_orient == "horizontal":
                img = img.rotate(-90, expand=True)

            for _c in range(copies):
                all_photos.append(img)
        except ValueError as e:
            err_str = str(e)
            if "410" in err_str or "face" in err_str.lower():
                return {"error": "face_detection_failed"}, 410
            elif "429" in err_str or "quota" in err_str.lower():
                return {"error": "quota_exceeded"}, 429
            elif "api_key" in err_str.lower() or "unauthorized" in err_str.lower():
                return {"error": "invalid_api_key"}, 401
            else:
                return {"error": err_str}, 500

    # ---- Layout engine ----
    pages = layout_mixed_flow(all_photos, a4_w, a4_h, gap, margin_x, margin_y, photos_per_page)
    if not pages:
        pages = [Image.new("RGB", (a4_w, a4_h), "white")]

    print(f"DEBUG: Total pages = {len(pages)}")

    # Export multi-page PDF
    output = BytesIO()
    if len(pages) == 1:
        pages[0].save(output, format="PDF", dpi=(dpi, dpi))
    else:
        pages[0].save(
            output,
            format="PDF",
            dpi=(dpi, dpi),
            save_all=True,
            append_images=pages[1:],
        )
    output.seek(0)
    print("DEBUG: Returning PDF to client")

    return send_file(
        output,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="passport-sheet.pdf",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)