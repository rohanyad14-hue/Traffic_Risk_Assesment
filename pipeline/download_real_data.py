import os
import urllib.request
import zipfile
import io
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_RAW_DIR = os.path.join(BASE_DIR, "data", "real_raw")
os.makedirs(REAL_RAW_DIR, exist_ok=True)

COLLISION_URL = "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-collision-2022.csv"
VEHICLE_URL = "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-vehicle-2022.csv"
AADF_ZIP_URL = "https://storage.googleapis.com/dft-statistics/road-traffic/downloads/data-gov-uk/dft_traffic_counts_aadf.zip"

def download_file(url, target_path):
    if os.path.exists(target_path):
        print(f"File already exists: {target_path} ({os.path.getsize(target_path)} bytes)")
        return target_path
    print(f"Downloading {url} -> {target_path} ...")
    t0 = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(target_path, "wb") as f:
        shutil_size = 0
        while True:
            chunk = resp.read(1024 * 512)
            if not chunk:
                break
            f.write(chunk)
            shutil_size += len(chunk)
    t1 = time.time()
    print(f"Downloaded {shutil_size} bytes in {t1 - t0:.1f}s.")
    return target_path

collision_file = os.path.join(REAL_RAW_DIR, "dft_collisions_2022.csv")
vehicle_file = os.path.join(REAL_RAW_DIR, "dft_vehicles_2022.csv")
aadf_zip_file = os.path.join(REAL_RAW_DIR, "dft_traffic_counts_aadf.zip")
aadf_csv_file = os.path.join(REAL_RAW_DIR, "dft_traffic_counts_aadf.csv")

download_file(COLLISION_URL, collision_file)
download_file(VEHICLE_URL, vehicle_file)
download_file(AADF_ZIP_URL, aadf_zip_file)

if not os.path.exists(aadf_csv_file):
    print("Extracting dft_traffic_counts_aadf.csv from zip...")
    with zipfile.ZipFile(aadf_zip_file) as z:
        z.extract("dft_traffic_counts_aadf.csv", REAL_RAW_DIR)
    print("Extracted AADF CSV successfully.")

print("All real raw files ready in:", REAL_RAW_DIR)
