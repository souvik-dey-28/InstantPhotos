# 📸 InstantPhotos: Ultimate Passport Maker

A powerful, **fully-offline capable** Flask application for automatically removing backgrounds, cropping, adjusting, and laying out passport photos perfectly onto A4/Letter/4x6 print sheets.

![InstantPhotos App](https://i.imgur.com/G5K5z2S.png)

## ✨ Features

- **100% Free Local AI Background Removal:** Uses `rembg` (U2Net AI model) running locally on your computer. No API keys, no internet requried, no daily quotas! 
- **Smart 2D Auto-Layout Engine:** Mix and match **Portrait (Vertical)** and **Landscape (Horizontal)** photos. The layout algorithm wraps them perfectly onto the exact same sheet, saving maximum paper.
- **Per-Photo Control:** Upload multiple different photos and set the exact copies and orientation (Portrait/Landscape) for each individual card.
- **Built-in Cropper:** Crop photos exactly to standard passport dimensions right in the browser.
- **Global Print Options:** Select DPI (150/300/600), Paper Size (A4, Letter, 4x6), and exact photo millimeters/pixels.
- **(Optional) AI Enhancement:** If you want extra sharpness and quality, you can add free Cloudinary API keys to enable automatic AI photo restoration.

---

## 🚀 Easy Installation Guide (Windows)

Follow these steps exact to run the app on Windows without errors.

### 1. Requirements
Make sure you have [Python 3.8+](https://www.python.org/downloads/) installed. During installation, make sure you check the box **"Add Python to PATH"**.

### 2. Setup the Project
Open **PowerShell** or **Command Prompt**, go to the folder where you downloaded this code, and run these commands:

```powershell
# 1. Create a virtual environment (keeps everything clean)
python -m venv venv

# 2. Activate the virtual environment
venv\Scripts\activate

# 3. Install all the required packages (this includes the local AI)
pip install -r requirements.txt
```

*(Note: If you get a green or red `execution of scripts is disabled` error when running step 2, open a fresh PowerShell as Administrator and run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then try again).*

### 3. First Time Running (Setup & Start)

After installing the packages in Step 2, run the app for the very first time:

```powershell
python app.py
```

- Open your browser and go to: **[http://localhost:5000](http://localhost:5000)**
- *Note:* The very first time you generate a photo, it will take 10–20 seconds because it needs to download the `rembg` AI model (176 MB) to your PC. After that, perfectly instant!

### 4. Running the App Later (2nd Time Onwards)

When you close your terminal and want to run the app again the next day, you **do not** need to install everything again. Just open terminal in the project folder and type:

```powershell
venv\Scripts\activate
python app.py
```
Then open **[http://localhost:5000](http://localhost:5000)** in your browser!

---

## 🔑 (Optional) Enable Cloudinary AI Enhancement

By default, the app applies basic local sharpening to photos so it works 100% offline. If you want **studio-quality AI restoration**, you can connect a free Cloudinary account. 

1. Sign up for free at [Cloudinary.com](https://cloudinary.com/).
2. Go to your Dashboard and get your **Cloud Name**, **API Key**, and **API Secret**.
3. Create a file named **exactly** `.env` in the root folder of this project.
4. Paste your keys like this:

```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```
Restart the app. The app will automatically detect these keys and route your photos through Cloudinary's `gen_restore` AI model for maximum quality!

---

## 🛠️ Troubleshooting

**Issue:** "API keys missing" warning in the terminal.
**Fix:** Ignore it! The app is designed to work fully offline and bypasses the APIs if you don't provide them.

**Issue:** `ModuleNotFoundError: No module named 'flask'` (or rembg/PIL).
**Fix:** You forgot to activate the virtual environment. Always run `venv\Scripts\activate` before running `python app.py`.

**Issue:** The "Both" orientation button is missing?
**Fix:** A photo can only be Portrait or Landscape. If you want a sheet with both types, just set some cards to Portrait and some to Landscape — they will automatically print together on the exact same page!
