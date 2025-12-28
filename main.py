import requests
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Drone Safety API")

class Point(BaseModel):
    latitude: float
    longitude: float

class DroneFlightRequest(BaseModel):
    flight_path: List[Point]
    safe_wind_speed: float
    drone_velocity: float

def get_weather_data(lat: float, lon: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["wind_speed_10m"],
        "wind_speed_unit": "ms",
        "timezone": "auto"
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        return {
            "wind_speed": data['current']['wind_speed_10m'],
            "time": data['current']['time']
        }
    except Exception:
        return None

@app.post("/check-flight-safety")
async def check_safety(request: DroneFlightRequest):
    if not request.flight_path:
        return None

    path_analysis = []

    for i, point in enumerate(request.flight_path):
        weather = get_weather_data(point.latitude, point.longitude)

        if not weather:
            path_analysis.append({
                "point": i + 1,
                "status": "ERROR",
                "msg": "Không có dữ liệu thời tiết"})
            continue

        current_wind = weather['wind_speed']
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
            "time_obs": weather['time'],
            "point_status": point_status,
            "notes": point_analysis
        })

    return {
        "detailed_report": path_analysis
    }