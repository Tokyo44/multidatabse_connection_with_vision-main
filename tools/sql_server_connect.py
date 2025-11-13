import contextlib
import sqlite3
import pandas as pd
from pathlib import Path

try:
    import streamlit as st
except ModuleNotFoundError:  # allow running outside Streamlit
    st = None

# SQLite database path
DB_PATH = (Path(__file__).resolve().parent.parent / "dvla.db").resolve()


def notify(message: str) -> None:
    if st is not None:
        st.info(message)
    else:
        print(message)


def show_success(message: str) -> None:
    if st is not None:
        st.success(message)
    else:
        print(message)


def show_error(message: str) -> None:
    if st is not None:
        st.error(message)
    else:
        print(message)


def show_table(df: pd.DataFrame, title: str = "Query Results") -> None:
    if st is not None:
        st.markdown("---")
        st.subheader(title)
        st.caption(f"Showing {len(df)} rows")
        height = min(600, 120 + len(df) * 35)
        # Remove the column padding to make table full width
        st.dataframe(df, use_container_width=True, height=height)
    else:
        print(df)


def main(license_number: str = None, first_name: str = None, last_name: str = None) -> None:
    try:
        if not DB_PATH.exists():
            show_error(f"Database not found at: {DB_PATH}")
            show_error("Please run 'tools/create_database.py' to create the database first.")
            return
        
        notify(f"Connecting to DVLA Database at {DB_PATH.name}...")
        with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
            show_success("Connected successfully to DVLA Database.")
            
            # Build query based on available information
            if license_number:
                # Search by license number with fuzzy matching - show top 5 matches
                query = f"""
                SELECT *, 
                       CASE 
                           WHEN license_number = '{license_number}' THEN 100
                           WHEN license_number LIKE '{license_number}%' THEN 90
                           WHEN license_number LIKE '%{license_number}%' THEN 80
                           ELSE 50
                       END as match_score
                FROM drivers 
                WHERE license_number LIKE '%{license_number}%'
                  AND status = 'active' 
                ORDER BY match_score DESC, expiry_date DESC
                LIMIT 5;
                """
                notify(f"Searching for license number: {license_number}")
            elif first_name and last_name:
                # Search by name with similarity scoring - show top 5 matches
                first_name_clean = first_name.replace("'", "''")  # Escape quotes
                last_name_clean = last_name.replace("'", "''")
                
                # More flexible matching: check if the database name contains the OCR name or vice versa
                query = f"""
                SELECT *, 
                       CASE 
                           WHEN LOWER(first_name) = LOWER('{first_name_clean}') AND LOWER(last_name) = LOWER('{last_name_clean}') THEN 100
                           WHEN LOWER(last_name) = LOWER('{last_name_clean}') AND 
                                (LOWER(first_name) LIKE LOWER('%{first_name_clean}%') OR 
                                 LOWER('{first_name_clean}') LIKE LOWER('%' || SUBSTR(first_name, 1, 4) || '%')) THEN 90
                           WHEN LOWER(last_name) = LOWER('{last_name_clean}') THEN 80
                           WHEN LOWER(last_name) LIKE LOWER('%{last_name_clean}%') OR 
                                LOWER('{last_name_clean}') LIKE LOWER('%' || last_name || '%') THEN 70
                           ELSE 50
                       END as match_score
                FROM drivers 
                WHERE LOWER(last_name) = LOWER('{last_name_clean}')
                  AND status = 'active'
                ORDER BY match_score DESC, expiry_date DESC
                LIMIT 5;
                """
                notify(f"Searching for driver: {first_name} {last_name}")
            else:
                # Fallback: show sample records
                query = "SELECT * FROM drivers LIMIT 5;"
                notify("No specific driver info provided. Showing sample records...")
            
            df = pd.read_sql(query, conn)
            
            if len(df) == 0:
                show_error("No matching driver records found in the database.")
            else:
                show_success(f"Retrieved {len(df)} driver record(s). Displaying below.")
                show_table(df, title="Driver Information")
    except Exception as exc:  # broad catch to surface errors in Streamlit UI
        show_error(f"Database error: {exc}")


if __name__ == "__main__":
    main()

