import pandas as pd
import streamlit as st
import googlemaps

st.title("Driving Distance Calculator (ZIP to ZIP via Google Maps API)")

# Step 1: Upload ZIP file
uploaded_file = st.file_uploader("Upload ZIP.csv (must include column 'To Zip')", type=["csv"])

# Step 2: Input your API key
api_key = st.text_input("Enter your Google Maps API Key", type="password")

# Step 3: Hardcoded default "From Zip" list
default_from_zips = [z.zfill(5) for z in ['52806', '46168', '42307', '60446', '91730']]
st.markdown(f"**Default From ZIP codes:** `{', '.join(default_from_zips)}`")

if uploaded_file is not None and api_key:
    # Read the uploaded CSV and normalize ZIPs
    df_template = pd.read_csv(uploaded_file, dtype={'To Zip': str})
    df_template['To Zip'] = df_template['To Zip'].fillna('').str.zfill(5)
    to_zips = df_template['To Zip'].unique()

    # Initialize Google Maps API client
    gmaps = googlemaps.Client(key=api_key)

    # Create combinations of all From x To ZIPs
    pairs = [(src, dst) for src in default_from_zips for dst in to_zips]
    results = []

    st.info("Querying Google Maps for driving distances...")

    for origin, destination in pairs:
        try:
            matrix = gmaps.distance_matrix(origins=origin, destinations=destination, mode="driving")
            element = matrix['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                miles = element['distance']['value'] / 1609.34  # meters to miles
                duration = element['duration']['text']
            else:
                miles = None
                duration = None
        except Exception:
            miles = None
            duration = None
        results.append({
            "From Zip": origin,
            "To Zip": destination,
            "Driving Distance (miles)": round(miles, 1) if miles else None,
            "Estimated Duration": duration
        })

    df_result = pd.DataFrame(results)
    st.success("✅ Done calculating driving distances!")
    st.dataframe(df_result)

    csv = df_result.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download results as CSV", csv, file_name="driving_distances.csv", mime="text/csv")

elif uploaded_file and not api_key:
    st.warning("🔐 Please enter your Google Maps API key.")
else:
    st.info("📂 Please upload a ZIP.csv file to continue.")
