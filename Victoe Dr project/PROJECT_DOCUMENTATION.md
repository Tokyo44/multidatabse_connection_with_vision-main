# ID Verification — Short Documentation

Purpose: Lightweight OCR-based ID verification. Upload an ID image, extract text with Tesseract, and match against the local `dvla.db` SQLite database.

Quick start
- Create and activate a Python virtualenv and install deps:

```bash
cd /Users/mac/Downloads/multidatabse_connection_with_vision-main
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Run the web UI:

```bash
streamlit run tools/streamlit_login.py
```

What’s inside
- `tools/streamlit_login.py` — Streamlit UI
- `tools/id_card_matcher_ocr.py` — OCR and extraction
- `tools/sql_server_connect.py` — SQLite access (`dvla.db`)

Notes
- Minimum confidence to allow login: 40%
- Training/old ML files moved to `didnotuse_*` and `didnotuse_id_cards/`

Contact
- Author: Tokyo

End.
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
