import streamlit as st
import pandas as pd
import googlemaps
import time
from io import BytesIO

st.title("ZIP Code Driving Distance Calculator")
st.markdown(
    "Enter one or more origin ZIP codes and upload an Excel/CSV of destination ZIPs, then calculate driving distances."
)

# User input for origin ZIPs (comma-separated)
origin_input = st.text_input(
    "Enter origin ZIP codes (comma-separated)",
    value="52806,46168,42307,60446,91730"
)
origin_zips = [z.strip() for z in origin_input.split(",") if z.strip()]

# File uploader for destinations
uploaded_file = st.file_uploader(
    "Upload destination ZIP list (Excel or CSV)",
    type=["xlsx", "xls", "csv"]
)

api_key = st.text_input("Google Maps API Key", type="password")

if uploaded_file and api_key and origin_zips:
    # Read the uploaded file
    try:
        if uploaded_file.name.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file, dtype=str)
        else:
            df = pd.read_csv(uploaded_file, dtype=str)
    except Exception as e:
        st.error(f"Error reading file: {e}")
    else:
        if "To Zip" not in df.columns:
            st.error("Uploaded file must contain a 'To Zip' column.")
        else:
            dest_zips = df["To Zip"].dropna().unique().tolist()
            gmaps = googlemaps.Client(key=api_key)
            rows = []
            BATCH_SIZE = 20
            total = len(origin_zips) * len(dest_zips)
            done = 0
            progress = st.progress(0)

            for o in origin_zips:
                for i in range(0, len(dest_zips), BATCH_SIZE):
                    batch = dest_zips[i : i + BATCH_SIZE]
                    try:
                        result = gmaps.distance_matrix(
                            origins=[o],
                            destinations=batch,
                            mode="driving",
                            units="imperial"
                        )
                    except Exception as e:
                        st.error(f"API error: {e}")
                        st.stop()

                    for dest_entry, element in zip(batch, result["rows"][0]["elements"]):
                        if element.get("status") == "OK":
                            dist_val = element["distance"]["value"] / 1609.34
                            rows.append({
                                "Origin ZIP": o,
                                "Destination ZIP": dest_entry,
                                "Driving Distance (mi)": round(dist_val, 2)
                            })
                        else:
                            rows.append({
                                "Origin ZIP": o,
                                "Destination ZIP": dest_entry,
                                "Driving Distance (mi)": None
                            })
                    done += len(batch)
                    progress.progress(done / total)
                    time.sleep(1)

            out_df = pd.DataFrame(rows)
            # Convert to Excel in-memory
            buffer = BytesIO()
            out_df.to_excel(buffer, index=False)
            buffer.seek(0)
            st.success("Calculation complete!")
            st.download_button(
                label="Download Excel",
                data=buffer,
                file_name="zip_driving_distances.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    if not origin_zips:
        st.info("Please enter at least one origin ZIP code.")
    elif not uploaded_file:
        st.info("Upload a destination ZIP list to proceed.")
    elif not api_key:
        st.info("Enter your Google Maps API key.")
