**My Understanding Of The Project — By Yaa Amoani Abban**

Purpose (in one line):
- This project is a simple ID verification tool that uses OCR (Tesseract) to read text from an uploaded ID image and then checks that text against a local SQLite database (`dvla.db`) to find matching driver records.

Overview (simple):
- You upload a photo of an ID (driver license, voter ID, Ghana card).
- The app runs OCR on the image to extract text.
- Extracted text is searched using fuzzy rules against a local SQLite database of drivers.
- If the match confidence is high enough, the user is considered verified.

Quick start (short commands):
```
cd /Users/mac/Downloads/multidatabse_connection_with_vision-main
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run tools/streamlit_login.py
```

Files you should know:
- `tools/streamlit_login.py` — the web UI that runs in Streamlit.
- `tools/id_card_matcher_ocr.py` — OCR extraction and text parsing logic.
- `tools/sql_server_connect.py` — code that opens and queries the local SQLite database (`dvla.db`).
- `PROJECT_DOCUMENTATION.md` — full project documentation (more details).

How it works (plain language):
- Step 1: The app asks you to upload an ID picture.
- Step 2: Tesseract OCR converts the picture into plain text.
- Step 3: The code looks for keywords (names, ID numbers) and computes a confidence score.
- Step 4: Using fuzzy matching rules (exact last-name match, first-name scoring, small boosts for strong matches), it compares the extracted text against entries in `dvla.db`.
- Step 5: If confidence ≥ 40% and card type is recognized, login/verification is allowed.

Important notes (keep in mind):
- Minimum confidence to allow login is 40% — this prevents false positives.
- Tesseract must be installed on your machine (`tesseract --version`).
- If images are low quality or rotated, OCR accuracy drops; try a clearer photo.
- Large binary files (images) are present in the repository; pushing to GitHub may require `git lfs` if files exceed 100 MB.

Simple troubleshooting:
- OCR returns empty or poor text: check `tesseract --version` and try a clearer image.
- No database matches: check names in `dvla.db` with `sqlite3 dvla.db 'SELECT * FROM drivers WHERE last_name="NAME";'` and verify the extracted text.
- Login button disabled: make sure confidence ≥ 40% and the app detected a known card type.

What I (Yaa) should remember:
- This is OCR-first (no ML training needed), so image quality is the most important factor.
- The app is intended to run locally — it uses a local SQLite database and Streamlit UI.

Contact / Where to look next:
- Open `tools/streamlit_login.py` to see the UI behavior.
- Review `PROJECT_DOCUMENTATION.md` for full details and troubleshooting.

End — a small, simple summary to help Yaa understand and run the project.
