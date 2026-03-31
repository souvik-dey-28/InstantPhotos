import os
from io import BytesIO
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from PIL import Image, ImageOps, ImageEnhance

# Lazy load rembg to show it's used safely
try:
    from rembg import remove
except ImportError:
    remove = None

app = Flask(__name__)

# Security: Limit maximum upload size to 16MB Total (Blue Team approach)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Security: Prevent decompression bombs
Image.MAX_IMAGE_PIXELS = 100000000  # limit to ~100 megapixels

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return {"error": "File size exceeds the 16MB limit. Please upload a smaller image."}, 413

@app.errorhandler(Exception)
def handle_exception(e):
    # Log the internal error safely but return generic message
    print(f"Internal Error: {e}")
    return {"error": "An internal server error occurred while processing the request."}, 500

@app.route("/")
def index():
    return render_template("index.html")

def process_single_image(input_image_bytes):
    """Remove background locally, enhance, and return a ready-to-paste passport PIL image."""
    if not remove:
        raise ValueError("rembg library is not installed. Please install it to use background removal.")
        
    try:
        # Security: Validate it's an image first before deep processing
        img_check = Image.open(BytesIO(input_image_bytes))
        img_check.verify() # Verify it is an image
    except Exception:
        raise ValueError("Invalid image file provided.")

    # Step 1: Background removal using local rembg
    try:
        # remove() expects raw bytes or a PIL image. Using raw bytes directly.
        bg_removed_bytes = remove(input_image_bytes)
        img = Image.open(BytesIO(bg_removed_bytes))
    except Exception as e:
        print(f"Local bg removal error: {e}")
        raise ValueError("local_bg_removal_failed")

    if img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        processed_img = background
    else:
        processed_img = img.convert("RGB")

    # Step 2: Local Enhancement (Sharpening)
    try:
        enhancer = ImageEnhance.Sharpness(processed_img)
        # Apply a mild sharpening factor (1.0 is original, 1.5 is slightly sharpened)
        passport_img = enhancer.enhance(1.5)
        
        # Optionally contrast boost
        contrast = ImageEnhance.Contrast(passport_img)
        passport_img = contrast.enhance(1.05)
    except Exception as e:
        print(f"Local enhancement error: {e}")
        passport_img = processed_img

    return passport_img

@app.route("/process", methods=["POST"])
def process():
    print("==== /process endpoint hit ====")

    # Layout settings
    try:
        passport_width = int(request.form.get("width", 390))
        passport_height = int(request.form.get("height", 480))
        border = int(request.form.get("border", 2))
        spacing = int(request.form.get("spacing", 10))
    except ValueError:
        return {"error": "Invalid form parameters."}, 400
        
    margin_x = 10
    margin_y = 10
    horizontal_gap = 10
    a4_w, a4_h = 2480, 3508

    # Collect images safely
    images_data = []

    # Multi-image mode
    i = 0
    while f"image_{i}" in request.files:
        file = request.files[f"image_{i}"]
        if file.filename:
            # We don't save to disk, but checking filename presence is good practice
            secure_name = secure_filename(file.filename)
            try:
                copies = int(request.form.get(f"copies_{i}", 6))
            except ValueError:
                copies = 6
            images_data.append((file.read(), copies))
        i += 1

    # Fallback to single image mode
    if not images_data and "image" in request.files:
        file = request.files["image"]
        if file.filename:
             try:
                 copies = int(request.form.get("copies", 6))
             except ValueError:
                 copies = 6
             images_data.append((file.read(), copies))

    if not images_data:
        return {"error": "No image uploaded or invalid file name."}, 400

    print(f"DEBUG: Processing {len(images_data)} image(s)")

    # Process all images
    passport_images = []
    for idx, (img_bytes, copies) in enumerate(images_data):
        print(f"DEBUG: Processing image {idx + 1} with {copies} copies")
        try:
            img = process_single_image(img_bytes)
            img = img.resize((passport_width, passport_height), Image.LANCZOS)
            img = ImageOps.expand(img, border=border, fill="black")
            passport_images.append((img, copies))
        except ValueError as e:
            err_str = str(e)
            if "invalid image" in err_str.lower():
                return {"error": "Corrupted or unsupported image uploaded."}, 415
            else:
                print(f"Processing error: {err_str}")
                return {"error": "Failed to process image."}, 500

    if not passport_images:
        return {"error": "No valid images processed."}, 400

    paste_w = passport_width + 2 * border
    paste_h = passport_height + 2 * border

    # Build all pages
    pages = []
    current_page = Image.new("RGB", (a4_w, a4_h), "white")
    x, y = margin_x, margin_y

    def new_page():
        nonlocal current_page, x, y
        pages.append(current_page)
        current_page = Image.new("RGB", (a4_w, a4_h), "white")
        x, y = margin_x, margin_y

    for passport_img, copies in passport_images:
        for _ in range(copies):
            if x + paste_w > a4_w - margin_x:
                x = margin_x
                y += paste_h + spacing

            if y + paste_h > a4_h - margin_y:
                new_page()

            current_page.paste(passport_img, (x, y))
            x += paste_w + horizontal_gap

    pages.append(current_page)
    print(f"DEBUG: Total pages = {len(pages)}")

    output = BytesIO()
    if len(pages) == 1:
        pages[0].save(output, format="PDF", dpi=(300, 300))
    else:
        pages[0].save(
            output,
            format="PDF",
            dpi=(300, 300),
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
    is_debug = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")
    app.run(host="0.0.0.0", port=5000, debug=is_debug)