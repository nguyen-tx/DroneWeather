import json
import math
from typing import List

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Drone Safety API")


class Point(BaseModel):
    latitude: float
    longitude: float


class DroneFlightRequest(BaseModel):
    flight_path: List[Point]
    safe_wind_speed: float
    drone_velocity: float


def find_nearest_region(lat, lon, file_position="vn_position.json"):
    try:
        with open(file_position, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Lỗi: Chưa có file dữ liệu tọa độ.")
        return None

    nearest_url = None
    min_distance = float('inf')

    for url, coords in data.items():
        dist = math.sqrt((coords['lat'] - lat) ** 2 + (coords['lon'] - lon) ** 2)

        if dist < min_distance:
            min_distance = dist
            nearest_url = url

    return nearest_url


def get_weather_data(lat: float, lon: float):
    url = find_nearest_region(lat, lon)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, "html.parser")
        grids = soup.find_all("div", class_="uk-width-3-4")
        wind_speed = grids[6].get_text().split("tốc độ:")[-1].strip()[:1]
        return wind_speed

    except Exception as e:
        print(e)

@app.post("/check-flight-safety")
async def check_safety(request: DroneFlightRequest):
    if not request.flight_path:
        return None

    path_analysis = []

    for i, point in enumerate(request.flight_path):
        wind_speed = get_weather_data(point.latitude, point.longitude)

        if not wind_speed:
            path_analysis.append({
                "point": i + 1,
                "status": "ERROR",
                "msg": "Không có dữ liệu thời tiết"})
            continue

        current_wind = float(wind_speed)
        point_analysis = []
        point_status = "GREEN"

        if current_wind >= request.safe_wind_speed:
            point_status = "RED"
            point_analysis.append("Tốc độ gió vượt ngưỡng")
        else:
            point_analysis.append("Tốc độ gió ổn định")

        if current_wind > request.drone_velocity:
            point_analysis.append("Drone không thể tiến")

        path_analysis.append({
            "step": i + 1,
            "coords": {"lat": point.latitude, "lng": point.longitude},
            "wind_speed": f"{current_wind} m/s",
            "point_status": point_status,
            "notes": point_analysis
        })

    return {
        "detailed_report": path_analysis
    }
