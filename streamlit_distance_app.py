import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from math import radians, sin, cos, sqrt, atan2

# 1. Read your template CSV and preserve leading zeros
df_template = pd.read_csv('ZIP.csv', dtype={'From Zip': str, 'To Zip': str})
df_template['From Zip'] = df_template['From Zip'].str.zfill(5)
df_template['To Zip'] = df_template['To Zip'].str.zfill(5)

# 2. Expand to all 5 source ZIPs (also as 5-digit strings)
sources = ['52806', '46168', '42307', '60446', '91730']
sources = [z.zfill(5) for z in sources]
to_zips = df_template['To Zip'].unique()
df = pd.DataFrame(
    [(src, tgt) for src in sources for tgt in to_zips],
    columns=['From Zip', 'To Zip']
)

# 3. Use geopy to look up each ZIP’s lat/lon
geo = Nominatim(user_agent="zip-distance-calculator")
geocode = RateLimiter(geo.geocode, min_delay_seconds=1, max_retries=2)

def lookup_coord(zipcode):
    loc = geocode({'postalcode': zipcode, 'country': 'US'})
    if loc:
        return loc.latitude, loc.longitude
    else:
        return None, None

# Build a cache of coords
cache = {}
for z in set(df['From Zip']).union(df['To Zip']):
    cache[z] = lookup_coord(z)

# 4. Haversine distance
def haversine(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    R = 3958.8  # Earth radius in miles
    φ1, φ2 = radians(lat1), radians(lat2)
    dφ = radians(lat2 - lat1)
    dλ = radians(lon2 - lon1)
    h = sin(dφ/2)**2 + cos(φ1)*cos(φ2)*sin(dλ/2)**2
    return 2*R*atan2(sqrt(h), sqrt(1-h))

# 5. Compute and fill
distances = []
for _, row in df.iterrows():
    coord1 = cache[row['From Zip']]
    coord2 = cache[row['To Zip']]
    if None in coord1 or None in coord2:
        distances.append(None)
    else:
        distances.append(round(haversine(coord1, coord2), 1))

df['Distance on map in mile'] = distances

# 6. Save output
df.to_csv('ZIP_with_distances.csv', index=False)
print("✅ Done! Distances written to ZIP_with_distances.csv")
