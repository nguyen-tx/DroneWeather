from typing import List

import geopandas as gpd
import pandas as pd
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from pydantic import BaseModel
from shapely.geometry import LineString
from unidecode import unidecode

app = FastAPI(title="Drone Safety API")

class Point(BaseModel):
    latitude: float
    longitude: float


class DroneFlightRequest(BaseModel):
    flight_path: List[Point]
    safe_wind_speed: float
    drone_velocity: float

count=0
def format_provinces(input_str):
    result = unidecode(input_str)
    return result


def find_nearest_region(lat_a, lon_a, lat_b, lon_b):
    gdf = gpd.read_file("provinces.json")
    df_mapping = pd.read_csv("provinces.csv", header=None, names=['Province', 'URL'])
    mapping_dict = {format_provinces(row['Province']): row['URL'] for _, row in df_mapping.iterrows()}
    path_line = LineString([(lon_a, lat_a), (lon_b, lat_b)])
    mask = gdf.intersects(path_line)
    provinces_crossed = gdf[mask].copy()
    provinces_crossed['dist'] = provinces_crossed.geometry.apply(lambda g: path_line.project(g.centroid))
    provinces_crossed = provinces_crossed.sort_values(by='dist')
    matched_url = []
    for _, row in provinces_crossed.iterrows():
        province_name = row['Name']
        url = mapping_dict.get(province_name)
        matched_url.append(url)
    return matched_url


def get_weather_data(a: Point, b: Point):
    url = find_nearest_region(a.latitude, a.longitude, b.latitude, b.longitude)
    wind_speed = []
    for u in url:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            r = requests.get(u, headers=headers)
            r.encoding = 'utf-8'
            soup = BeautifulSoup(r.text, "html.parser")
            grids = soup.find_all("div", class_="uk-width-3-4")
            speed = grids[6].get_text().split("tốc độ:")[-1].strip()[:1]
            wind_speed.append(speed)
        except Exception as e:
            print(e)
    return wind_speed


@app.post("/check-flight-safety")
async def check_safety(request: DroneFlightRequest):
    global count
    if not request.flight_path:
        return None

    path_analysis = []

    for i in range(len(request.flight_path) - 1):
        point_a = request.flight_path[i]
        point_b = request.flight_path[i + 1]

        wind_speed = get_weather_data(point_a, point_b)
        print(wind_speed)
        if not wind_speed:
            path_analysis.append({
                "point": i + 1,
                "status": "ERROR",
                "msg": "Không có dữ liệu thời tiết"})
            continue
        for ws in wind_speed:
            count = count + 1
            current_wind = float(ws)
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
                "step": count,
                "wind_speed": f"{current_wind} m/s",
                "point_status": point_status,
                "notes": point_analysis
            })

    return {
        "detailed_report": path_analysis
    }
