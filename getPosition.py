import json
import re
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

INPUT_FILE = "province_urls.txt"
OUTPUT_FILE = "vn_position.json"

geolocator = Nominatim(user_agent="vn_weather_location_service")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.2)

def process_urls():
    results = {}
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Không tìm thấy file {INPUT_FILE}")
        return

    for index, url in enumerate(urls):
        match = re.search(r'/([^/]+)-w\d+\.html', url)
        if match:
            slug = match.group(1)
            search_query = slug.replace('-', ' ') + ", Vietnam"
            try:
                location = geocode(search_query)
                if not location:
                    parts = slug.split('-')
                    if len(parts) > 2:
                        fallback_query = " ".join(parts[-2:]) + ", Vietnam"
                        location = geocode(fallback_query)
                if location:
                    results[url] = {
                        "lat": location.latitude,
                        "lon": location.longitude,
                        "display_name": location.address
                    }
                else:
                    print(f"\nKhông tìm thấy tọa độ cho: {slug}")

            except Exception as e:
                print(e)

    # Lưu kết quả ra file JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    process_urls()
