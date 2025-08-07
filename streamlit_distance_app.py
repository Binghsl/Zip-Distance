import streamlit as st
import pandas as pd
import time
import requests
from io import BytesIO
import pgeocode

st.title("ZIP Code Driving Distance Calculator (GraphHopper API)")
st.markdown(
    "Enter one or more origin ZIP codes and upload an Excel/CSV of destination ZIPs, "
    "then calculate driving distances using the GraphHopper routing engine."
)

# Origin ZIP input
origin_input = st.text_input(
    "Enter origin ZIP codes (comma-separated)",
    value="42307"
)
origin_zips = [z.strip() for z in origin_input.split(",") if z.strip()]

# Upload ZIP list
uploaded_file = st.file_uploader(
    "Upload destination ZIP list (Excel or CSV with column 'To Zip')",
    type=["xlsx", "xls", "csv"]
)

# Load GraphHopper API key from secrets
api_key = st.secrets["GRAPH_HOPPER_API_KEY"] if "GRAPH_HOPPER_API_KEY" in st.secrets else ""

if uploaded_file and api_key and origin_zips:
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
            nomi = pgeocode.Nominatim("us")
            rows = []
            total = len(origin_zips) * len(dest_zips)
            done = 0
            progress = st.progress(0)

            def get_coords(zipcode):
                loc = nomi.query_postal_code(zipcode)
                if pd.isna(loc.latitude) or pd.isna(loc.longitude):
                    return None
                return (loc.latitude, loc.longitude)

            for o in origin_zips:
                o_coord = get_coords(o)
                if not o_coord:
                    st.warning(f"Could not find coordinates for origin ZIP {o}.")
                    continue
                for d in dest_zips:
                    d_coord = get_coords(d)
                    if not d_coord:
                        continue
                    try:
                        url = f"https://graphhopper.com/api/1/route"
                        params = {
                            "point": [f"{o_coord[0]},{o_coord[1]}", f"{d_coord[0]},{d_coord[1]}"],
                            "vehicle": "car",
                            "locale": "en",
                            "calc_points": "false",
                            "key": api_key
                        }
                        r = requests.get(url, params=params)
                        data = r.json()
                        if "paths" in data:
                            meters = data["paths"][0]["distance"]
                            miles = meters / 1609.34
                            rows.append({
                                "Origin ZIP": o,
                                "Destination ZIP": d,
                                "Driving Distance (mi)": round(miles, 2)
                            })
                        else:
                            rows.append({
                                "Origin ZIP": o,
                                "Destination ZIP": d,
                                "Driving Distance (mi)": None
                            })
                    except Exception:
                        rows.append({
                            "Origin ZIP": o,
                            "Destination ZIP": d,
                            "Driving Distance (mi)": None
                        })
                    done += 1
                    progress.progress(done / total)
                    time.sleep(0.1)

            out_df = pd.DataFrame(rows)
            buffer = BytesIO()
            out_df.to_excel(buffer, index=False)
            buffer.seek(0)
            st.success("Calculation complete!")
            st.download_button(
                label="Download Excel",
                data=buffer,
                file_name="zip_driving_distances_graphhopper.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    if not uploaded_file:
        st.info("Upload a destination ZIP list to proceed.")
    elif not api_key:
        st.warning("Missing GraphHopper API key in secrets. Add GRAPH_HOPPER_API_KEY to .streamlit/secrets.toml or Streamlit Cloud secrets.")
    elif not origin_zips:
        st.info("Please enter at least one origin ZIP code.")
