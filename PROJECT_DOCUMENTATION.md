# Government ID Verification System - Documentation

## Project Overview
An AI-powered ID card verification system that uses OCR (Optical Character Recognition) to identify and verify government-issued ID cards against a database of registered drivers.

**Technology Stack:**
- Python 3.13.7
- Streamlit 1.50.0 (Web UI)
- Tesseract OCR 5.5.1 (Text extraction)
- SQLite3 (Database)
- PIL/Pillow (Image processing)

---

## System Architecture

### 1. **Frontend: Streamlit Web Application**
   - **File:** `tools/streamlit_login.py`
   - **Purpose:** User interface for uploading ID cards and viewing results
   - **Features:**
     - Image upload (PNG, JPG, JPEG, BMP, GIF)
     - Two-step verification (Identify → Login)
     - Real-time confidence scoring
     - Database query results display

### 2. **OCR Engine**
   - **File:** `tools/id_card_matcher_ocr.py`
   - **Purpose:** Extract and analyze text from ID card images
   - **Capabilities:**
     - Image preprocessing (resize, enhance contrast, sharpen)
     - Multi-approach OCR (3 different configurations)
     - Card type identification via keyword matching
     - License number extraction
     - Name extraction (first and last)
   - **Supported ID Types:**
     - Drivers Licence (keywords: driver, licence, license, california, dmv, etc.)
     - Ghana Card (keywords: ghana, nia, national identification, etc.)
     - Voter ID (keywords: voter, electoral, commission, etc.)

### 3. **Database Layer**
   - **File:** `tools/sql_server_connect.py`
   - **Database:** `dvla.db` (SQLite)
   - **Purpose:** Store and query driver information
   - **Features:**
     - Fuzzy matching for OCR typos
     - Top 5 best matches with similarity scoring
     - Case-insensitive search

---

## How It Works

### Step 1: Upload ID Card
User uploads a photo of their government ID through the Streamlit interface.

### Step 2: OCR Processing
1. Image is preprocessed (enhanced, sharpened, upscaled)
2. Tesseract extracts text using multiple configurations
3. System searches for keywords to identify card type
4. Confidence score calculated (0-100%)

### Step 3: Information Extraction
- **License Number:** Regex patterns extract alphanumeric IDs
- **Name:** Pattern matching for first and last names
- **OCR Error Correction:** Converts common mistakes (O→0, I→1)

### Step 4: Database Verification
1. Query database using extracted information
2. Fuzzy matching handles OCR typos
3. Returns top 5 closest matches ranked by similarity
4. Display driver details in a table

---

## Database Schema

**Table: `drivers`**

| Column         | Type    | Description                          |
|----------------|---------|--------------------------------------|
| driver_id      | INTEGER | Primary key (auto-increment)         |
| license_number | TEXT    | Unique license identifier            |
| first_name     | TEXT    | Driver's first name                  |
| last_name      | TEXT    | Driver's last name                   |
| date_of_birth  | DATE    | DOB (YYYY-MM-DD)                     |
| issue_date     | DATE    | License issue date                   |
| expiry_date    | DATE    | License expiration date              |
| address        | TEXT    | Full address                         |
| license_class  | TEXT    | License class (C, CHILD, etc.)       |
| status         | TEXT    | 'active' or 'inactive'               |

**Current Records:** 20 drivers from CA, IL, TX, NY, FL

---

## Installation & Setup

### Prerequisites
```bash
# Install Homebrew (macOS)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Tesseract OCR
brew install tesseract
```

### Python Environment
```bash
# Navigate to project
cd /Users/mac/Downloads/multidatabse_connection_with_vision-main

# Create virtual environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Required Packages
- streamlit==1.50.0
- pytesseract
- Pillow==11.3.0
- pandas==2.3.3
- numpy

---

## Usage

### Run the Application
```bash
# Activate virtual environment
source .venv/bin/activate

# Start Streamlit app
streamlit run tools/streamlit_login.py
```

### Access the Application
- **Local URL:** http://localhost:8501
- **Network URL:** http://172.20.10.2:8501

### Using the System
1. Open browser to http://localhost:8501
2. Upload an ID card image
3. Click **"🔍 Identify Card Type"**
4. View OCR confidence and extracted information
5. Click **"🔐 Log In"** (enabled when confidence ≥ 40%)
6. View matching driver records from database

---

## Configuration

### Confidence Threshold
- **Minimum:** 40% (hardcoded in `tools/streamlit_login.py`)
- **Purpose:** Ensures reliable identification before allowing login
- **Calculation:** Keyword match score with bonus for strong matches

### OCR Settings
- **Image preprocessing:** Contrast 2.5x, Brightness 1.2x, Triple sharpening
- **Minimum image size:** 1000px (auto-upscaled)
- **PSM modes:** 6 (uniform block) and 3 (fully automatic)

### Database Search
- **Match scoring:** 100 (exact) → 90 (close) → 80 (partial) → 70 (contains)
- **Result limit:** Top 5 matches
- **Fuzzy matching:** Case-insensitive with partial string matching

---

## File Structure

```
multidatabse_connection_with_vision-main/
├── .venv/                          # Python virtual environment
├── dvla.db                         # SQLite database (20 drivers)
├── temp_ocr/                       # Temporary OCR processing files
├── requirements.txt                # Python dependencies
├── README.md                       # Original project README
├── PROJECT_DOCUMENTATION.md        # This file
│
├── tools/
│   ├── streamlit_login.py         # ✅ Main Streamlit UI
│   ├── id_card_matcher_ocr.py     # ✅ OCR engine
│   ├── sql_server_connect.py      # ✅ Database queries
│   │
│   └── notinuse_*.py              # ❌ Old ML-related files (7 files)
│
└── notinuse_id_cards/             # ❌ Old ML training dataset
```

---

## Database Management

### View All Drivers
```bash
sqlite3 dvla.db "SELECT first_name, last_name, license_number FROM drivers;"
```

### Count Drivers
```bash
sqlite3 dvla.db "SELECT COUNT(*) FROM drivers;"
```

### Add New Driver
```bash
sqlite3 dvla.db "
INSERT INTO drivers (license_number, first_name, last_name, date_of_birth, issue_date, expiry_date, address, license_class, status) 
VALUES ('CA123456789', 'John', 'Doe', '1990-01-01', '2020-01-01', '2028-01-01', '123 Main St, CA 90001', 'C', 'active');
"
```

### Search by Name
```bash
sqlite3 dvla.db "SELECT * FROM drivers WHERE last_name = 'Stewart';"
```

---

## Technical Details

### OCR Accuracy Improvements
1. **Image Enhancement:**
   - Upscale small images to 1000px minimum
   - Enhance contrast by 2.5x
   - Increase brightness by 1.2x
   - Apply triple sharpening (SHARPEN filter + UnsharpMask)

2. **Multi-Pass OCR:**
   - Pass 1: Preprocessed image with PSM 6
   - Pass 2: Original image with PSM 6
   - Pass 3: Preprocessed image with PSM 3
   - Combine all results

3. **Error Correction:**
   - O/o → 0 (letter O to zero)
   - I/l → 1 (letter I/l to one)

### Confidence Calculation
```python
# Base confidence
confidence = (keywords_found / total_keywords * 0.3) * 100

# Boost for strong matches (2+ exact keywords)
if score >= 4:
    confidence *= 1.5

# Minimum confidence if any keywords found
confidence = max(confidence, 40.0)
```

### Fuzzy Matching Strategy
1. **Exact last name match** (primary filter)
2. **First name similarity scoring:**
   - Exact match: 100 points
   - Contains substring: 90 points
   - Last name only: 80 points
3. **Case-insensitive throughout**

---

## Troubleshooting

### Issue: "No usable temporary directory"
**Solution:** Disk space issue. System creates temp files in `temp_ocr/` folder.
- Free up disk space (need 500MB+ free)
- Empty macOS Trash

### Issue: OCR confidence always 0%
**Solution:** 
- Check Tesseract installation: `tesseract --version`
- Verify image quality (not too blurry)
- Check keywords match card type

### Issue: Login button disabled
**Solution:**
- Confidence must be ≥ 40%
- Card type must not be "Unknown"
- Click "Identify" button first

### Issue: No database matches found
**Solution:**
- Check if driver exists: `sqlite3 dvla.db "SELECT * FROM drivers WHERE last_name='[NAME]';"`
- OCR may have misread name (check extracted text)
- Fuzzy matching handles typos, but severe errors may fail

---

## Migration from ML to OCR

**Previous System (Removed):**
- ResNet18 deep learning model
- Required training dataset (1000+ labeled images)
- pyodbc + SQL Server (Windows only)

**Current System (Active):**
- Tesseract OCR (no training needed)
- Works on any clear ID image
- SQLite (cross-platform, no server)

**Benefits:**
- ✅ No training data required
- ✅ Instant setup (just install Tesseract)
- ✅ Works on macOS/Linux/Windows
- ✅ Lower resource usage
- ✅ More interpretable results

---

## Future Enhancements

### Potential Improvements
1. **Multi-language OCR** - Support non-English IDs
2. **Face detection** - Verify photo matches uploaded ID
3. **Barcode scanning** - Extract data from 2D barcodes
4. **Mobile app** - React Native or Flutter frontend
5. **Cloud database** - PostgreSQL/MySQL for multi-user access
6. **Audit logging** - Track all verification attempts
7. **Admin dashboard** - Manage drivers, view analytics

### Performance Optimization
- Cache OCR results for identical images
- Parallel processing for batch uploads
- GPU acceleration for image preprocessing

---

## System Requirements

**Minimum:**
- macOS 10.15+ / Linux / Windows 10+
- Python 3.11+
- 2GB RAM
- 500MB free disk space

**Recommended:**
- macOS 12+ / Ubuntu 22.04+ / Windows 11
- Python 3.13+
- 4GB RAM
- 2GB free disk space
- Multi-core CPU for faster OCR

---

## License & Credits

**License:** MIT (see LICENSE file)

**Dependencies:**
- Streamlit (Apache 2.0)
- Tesseract OCR (Apache 2.0)
- Pillow (HPND License)
- Pandas (BSD 3-Clause)

**Author:** Tokyo (mac@tokyos-MacBook-Air)

**Last Updated:** November 9, 2025

---

## Contact & Support

For issues or questions:
1. Check this documentation
2. Review error messages in Streamlit UI
3. Check terminal output for detailed logs
4. Verify Tesseract installation: `tesseract --version`

---

*End of Documentation*
