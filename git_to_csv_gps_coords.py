import os
import re
import csv

def parse_lat_lon(value, direction):
    if not value or '.' not in value:
        return None
    degrees = int(value[:2])
    minutes = float(value[2:])
    decimal = degrees + minutes / 60.0
    if direction in ['S', 'W']:
        decimal = -decimal
    return round(decimal, 6)

def convert_git_to_csv(git_path, csv_path):
    with open(git_path, 'rb') as f:
        content = f.read()

    strings = re.findall(rb"[ -~]{4,}", content)
    decoded = [s.decode("utf-8", errors="ignore") for s in strings]

    gprmc = [s for s in decoded if s.startswith("$GPRMC")]
    gpgga = [s for s in decoded if s.startswith("$GPGGA")]

    rows = []
    for rmc, gga in zip(gprmc, gpgga):
        try:
            r = rmc.split(",")
            g = gga.split(",")

            time = r[1]
            date = r[9]
            timestamp = f"{date} {time}"

            lat = parse_lat_lon(r[3], r[4])
            lon = parse_lat_lon(r[5], r[6])
            speed = float(r[7]) * 1.852  # knots to km/h
            alt = float(g[9])

            rows.append([timestamp, lat, lon, round(speed, 2), alt])
        except:
            continue

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Latitude", "Longitude", "Speed (km/h)", "Altitude (m)"])
        writer.writerows(rows)

    print(f"CSV saved: {csv_path}")

input_folder = "/home/smlab/Desktop/dashcam/203gps/tar/tmp"

for filename in os.listdir(input_folder):
    if filename.endswith(".git"):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(input_folder, filename.replace(".git", ".csv"))
        convert_git_to_csv(input_path, output_path)
