from pathlib import Path

import streamlit as st

from id_card_matcher_ocr import OCRMatchResult, classify_id_ocr

SQL_CONNECT_SCRIPT = Path(__file__).resolve().parent / "sql_server_connect.py"
MINIMUM_CONFIDENCE = 40.0  # Minimum confidence percentage required to log in


def run_sql_server_demo(license_number: str = None, first_name: str = None, last_name: str = None) -> str:
    if not SQL_CONNECT_SCRIPT.exists():
        raise FileNotFoundError(f"SQL connector script not found at '{SQL_CONNECT_SCRIPT}'.")

    import io
    import sys
    from sql_server_connect import main as sql_main
    
    # Capture output
    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer
    
    try:
        sql_main(license_number=license_number, first_name=first_name, last_name=last_name)
    finally:
        sys.stdout = old_stdout
    
    return buffer.getvalue().strip()


def main() -> None:
    st.set_page_config(page_title="Image Login", page_icon="[img]", layout="centered")
    st.title("Government ID Verification")
    st.caption("Upload an ID card and we will identify it by reading the text on the card using OCR.")

    # Initialize session state for storing identification results
    if 'identification_result' not in st.session_state:
        st.session_state.identification_result = None
    if 'current_image_bytes' not in st.session_state:
        st.session_state.current_image_bytes = None

    uploaded_image = st.file_uploader(
        "Upload your ID image",
        type=["png", "jpg", "jpeg", "bmp", "gif"],
        accept_multiple_files=False,
    )

    if uploaded_image is not None:
        image_bytes = uploaded_image.read()
        st.image(image_bytes, caption="Uploaded image", use_container_width=True)
        
        # Check if a new image was uploaded
        if st.session_state.current_image_bytes != image_bytes:
            st.session_state.current_image_bytes = image_bytes
            st.session_state.identification_result = None  # Reset previous result
    else:
        image_bytes = None
        st.session_state.current_image_bytes = None
        st.session_state.identification_result = None

    # SQL database check toggle (using SQLite now)
    run_sql = st.toggle(
        "Run SQL check when Drivers Licence matches",
        value=True,
        help="Queries the SQLite database after a successful Drivers Licence match.",
    )

    # Step 1: Identify Card Type Button
    st.markdown("---")
    col_identify, col_login = st.columns(2)
    
    with col_identify:
        identify_button = st.button("🔍 Identify Card Type", use_container_width=True)
    
    with col_login:
        # Disable login if no result OR confidence below 40%
        can_login = (
            st.session_state.identification_result is not None and 
            st.session_state.identification_result.confidence >= MINIMUM_CONFIDENCE and
            st.session_state.identification_result.label != "Unknown"
        )
        login_button = st.button("🔐 Log In", type="primary", use_container_width=True, 
                                disabled=(not can_login))

    # Handle Identify button click
    if identify_button:
        if image_bytes is None:
            st.error("Please upload an ID image first.")
        else:
            with st.spinner("Extracting text and identifying card type..."):
                try:
                    result: OCRMatchResult = classify_id_ocr(image_bytes)
                    st.session_state.identification_result = result
                    st.rerun()  # Force page refresh to update login button state
                except FileNotFoundError as exc:
                    st.error(str(exc))
                    return
                except ModuleNotFoundError as exc:
                    st.error(f"Missing dependency: {exc}")
                    return
                except Exception as exc:  # pragma: no cover - safety net
                    import traceback
                    st.error(f"Classification failed: {exc}")
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())
                    return

    # Display identification results if available
    if st.session_state.identification_result is not None:
        result = st.session_state.identification_result
        
        st.markdown("---")
        st.subheader("📋 Identification Results")
        
        # Display OCR confidence slider (visual - updates automatically)
        st.slider(
            "📊 OCR Confidence Level",
            min_value=0.0,
            max_value=100.0,
            value=result.confidence,
            disabled=True,
            help=f"Current confidence from OCR detection. Minimum {MINIMUM_CONFIDENCE}% required to log in.",
        )
        
        col_card, col_conf = st.columns(2)
        with col_card:
            st.metric("Card Type Detected", result.label)
        with col_conf:
            st.metric("Confidence", f"{result.confidence:.1f}%")
        
        if result.keywords_found:
            st.info(f"**Keywords found:** {', '.join(result.keywords_found)}")
        
        # Always show extracted text for debugging
        with st.expander("📄 View Extracted Text", expanded=(result.confidence == 0)):
            if result.extracted_text.strip():
                st.text_area("OCR Output:", result.extracted_text, height=200)
                st.caption(f"Total characters extracted: {len(result.extracted_text)}")
            else:
                st.warning("⚠️ No text was extracted from the image. This could mean:")
                st.markdown("""
                - The image quality is too low
                - The text is too small or blurry
                - The image contains mostly graphics/photos
                - The contrast is too low
                
                **Tips:** Try uploading a clearer, higher resolution image.
                """)
        
        # Show status with 40% minimum threshold
        if result.confidence >= MINIMUM_CONFIDENCE and result.label != "Unknown":
            st.success(f"✅ Card identified as: **{result.label}**")
            
            # Show extracted driver info if available
            if result.label == "Drivers Licence":
                if result.license_number or result.first_name:
                    st.info("**Extracted Information:**")
                    if result.license_number:
                        st.write(f"📋 License Number: `{result.license_number}`")
                    if result.first_name and result.last_name:
                        st.write(f"👤 Name: `{result.first_name} {result.last_name}`")
        else:
            st.warning("⚠️ Low confidence identification")
            if result.label != "Unknown":
                st.info(f"Detected as '{result.label}' but confidence ({result.confidence:.1f}%) is below minimum threshold ({MINIMUM_CONFIDENCE}%).")
            else:
                st.error("❌ No recognizable ID card keywords found in the image.")
                st.info("**Expected keywords:** driver/licence, ghana/nia, voter/electoral")

    # Handle Login button click
    if login_button:
        if st.session_state.identification_result is None:
            st.error("Please identify the card first before logging in.")
            return
        
        result = st.session_state.identification_result
        
        st.markdown("---")
        st.subheader("🔐 Login Process")
        
        if result.confidence >= MINIMUM_CONFIDENCE and result.label != "Unknown":
            st.success(f"✅ **Login Successful!** Verified as: **{result.label}**")
            
            # Run SQL check if applicable
            if run_sql and result.label.lower() == "drivers licence":
                st.info("Drivers licence detected. Querying DVLA database...")
                
                # Show what we're searching for
                search_info = []
                if result.license_number:
                    search_info.append(f"License: {result.license_number}")
                if result.first_name and result.last_name:
                    search_info.append(f"Name: {result.first_name} {result.last_name}")
                
                if search_info:
                    st.caption(f"Searching by: {' | '.join(search_info)}")
                
                try:
                    output = run_sql_server_demo(
                        license_number=result.license_number,
                        first_name=result.first_name,
                        last_name=result.last_name
                    )
                    if output:
                        st.code(output, language="text")
                    else:
                        st.write("SQL script executed but returned no output.")
                except Exception as exc:
                    st.error(f"Database query failed: {exc}")
        else:
            st.error("❌ **Login Failed.** Could not confidently verify the ID card.")
            if result.label != "Unknown":
                st.info(f"Card detected as '{result.label}' but confidence ({result.confidence:.1f}%) is below the required minimum ({MINIMUM_CONFIDENCE}%).")
            else:
                st.warning("No valid ID card detected. Please upload a clear image of a Drivers Licence, Ghana Card, or Voter ID.")


if __name__ == "__main__":
    main()
