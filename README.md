# 📸 Passport Photo Pro

A web-based tool to generate print-ready passport photo sheets from uploaded images. Supports multiple photos, per-photo copy counts, AI background removal, image enhancement, and multi-page PDF export — all on an A4 layout at 300 DPI.

---

## 🚀 Features

- **Multi-photo upload** — drag & drop or click to upload one or more photos at once
- **Per-photo copy count** — set how many copies of each photo you need (1–54)
- **In-browser cropper** — crop each photo to the correct passport aspect ratio before processing
- **100% Free Local AI background removal** — powered by the open-source `rembg` library, no API keys required!
- **Local image enhancement** — automatically sharpens and enhances photos directly on your machine
- **A4 print layout** — photos are automatically arranged in a grid at 300 DPI
- **Multi-page PDF** — if photos exceed one A4 page, additional pages are created automatically
- **Secure File Handling (Blue Team verified)** — strong built-in limits for file sizes and payload protections
- **Feedback system** — built-in bug report form powered by EmailJS
- **Animated particle background** — via Particles.js

---

## 🧰 Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| Frontend  | HTML, Tailwind CSS, Vanilla JS    |
| Cropping  | Cropper.js                        |
| Backend   | Python, Flask                     |
| Image AI  | `rembg` (Background removal)      |
| PDF gen   | Pillow (PIL)                      |
| Security  | Flask limits, Werkzeug secure I/O |

---

## 📦 Prerequisites

- Python 3.8+
- pip
- An internet connection for the *first run only* (to download the background removal AI model)

---

## 🛠️ Step-by-Step Instructions

### ▶️ First Time Setup & Running

**1. Clone the repository**

```bash
git clone https://github.com/souvik-dey-28/InstantPhotos.git
cd InstantPhotos
```

**2. Create and connect to a virtual environment**

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

**3. Install all required dependencies**

```bash
pip install -r requirements.txt
```

**4. Start the Application**

```bash
python app.py
```
*Note: The first time you process an image, `rembg` will automatically download the AI model needed to remove backgrounds (around ~170MB). This may take a few moments depending on your network. Future uses will be instant and completely offline.*

The server will start at `http://localhost:5000`.

---

### 🛑 How to Stop the Program

When you are finished using the application, go back to the terminal (Command Prompt/PowerShell) where the server is running and press:
`Ctrl + C`
This will terminate the Flask server gracefully.

---

### 🔄 How to Run on Subsequent Times

To run the program again in the future, you do not need to reinstall anything. Follow these simple steps:

1. Open your terminal in the `InstantPhotos` folder.
2. Activate your virtual environment: 
   ```bash
   venv\Scripts\activate
   ```
3. Run the application: 
   ```bash
   python app.py
   ```

---

## 🖼️ How It Works

### Upload
- Open the app in your browser at `http://localhost:5000`
- Drag and drop one or more photos onto the upload zone, or click to browse

### Crop (Optional but Recommended)
- A modal cropper opens with a fixed passport aspect ratio (384×472)
- Adjust the crop area and click **Crop & Save**

### Generate
- The backend processes each photo locally:
  1. Validates the image securely.
  2. Removes the background via `rembg`.
  3. Enhances and sharpens via `PIL.ImageEnhance`.
  4. Resizes and adds a border.
- All photos are arranged on A4 pages (2480×3508 px at 300 DPI)
- If photos overflow one page, new pages are added automatically

### Download
- Once generated, click **Download PDF** to save the print-ready file.

---

## 🔐 Security Features

- The application uses `app.config['MAX_CONTENT_LENGTH']` to strictly limit user uploads (16 MB maximum) protecting against large payload Denial of Service attacks.
- File metadata is vetted and names are sanitized via `secure_filename`.
- Decompression bomb exploits are prevented by restricting `Image.MAX_IMAGE_PIXELS`.
- Internal errors are masked to prevent server logic leaking to clients during exceptions.

---

## 📬 Feedback & Bug Reports

Use the red chat button in the bottom-right corner of the app to submit feedback or report bugs directly from the UI.

---

## 📄 License

MIT License. See `LICENSE` for details.
