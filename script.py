from fastapi import FastAPI, Query
import uvicorn
import httpx
import sqlite3
from contextlib import closing
import asyncio
from datetime import datetime

app = FastAPI()

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
DB_NAME = "weather.db"

def init_db():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cities (
            name TEXT PRIMARY KEY,
            latitude REAL,
            longitude REAL
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS forecasts (
            city TEXT,
            time TEXT,
            temperature REAL,
            humidity REAL,
            wind_speed REAL,
            precipitation REAL,
            pressure REAL,
            PRIMARY KEY (city, time)
        )
        """)
        conn.commit()

def save_city(name: str, lat: float, lon: float):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO cities VALUES (?, ?, ?)",
            (name, lat, lon)
        )
        conn.commit()

def save_forecast(city: str, hourly_data: dict):
    times = hourly_data["time"]
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        for i in range(len(times)):
            cursor.execute("""
            INSERT OR REPLACE INTO forecasts 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                city,
                times[i],
                hourly_data["temperature_2m"][i],
                hourly_data["relative_humidity_2m"][i],
                hourly_data["wind_speed_10m"][i],
                hourly_data["precipitation"][i],
                hourly_data["surface_pressure"][i]
            ))
        conn.commit()

async def fetch_daily_forecast(lat: float, lon: float) -> dict:
    """Запрашивает почасовой прогноз на текущий день"""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,surface_pressure",
        "timezone": "auto"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(OPEN_METEO_URL, params=params)
        data = response.json()
        return data.get("hourly", {})

@app.get("/")
async def root():
    return {"status": "server is running"}

@app.get("/current-weather")
async def get_current_weather(
        latitude: float = Query(...),
        longitude: float = Query(...)
):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m,surface_pressure"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(OPEN_METEO_URL, params=params)
        data = response.json()
    current = data.get("current", {})
    return {
        "temperature": current.get("temperature_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "pressure": current.get("surface_pressure")
    }

@app.post("/add-city")
async def add_city(name: str, latitude: float, longitude: float):
    save_city(name, latitude, longitude)
    hourly_data = await fetch_daily_forecast(latitude, longitude)
    save_forecast(name, hourly_data)
    return {"message": f"City {name} added and forecast saved"}

@app.get("/cities")
async def get_cities():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM cities")
        rows = cursor.fetchall()
    return [row[0] for row in rows]


@app.get("/weather")
async def get_weather_by_time(
        city: str,
        time: str,
        fields: str
):
    selected_fields = fields.split(",")
    allowed = {
        "temperature": "temperature",
        "humidity": "humidity",
        "wind_speed": "wind_speed",
        "precipitation": "precipitation",
        "pressure": "pressure"
    }
    columns = [allowed[f] for f in selected_fields if f in allowed]
    if not columns:
        return {"error": "No valid fields selected"}
    sql = f"""
    SELECT {", ".join(columns)}
    FROM forecasts
    WHERE city = ? AND time LIKE ?
    """
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (city, f"%{time}%"))
        row = cursor.fetchone()
    if not row:
        return {"error": "No data found"}
    return dict(zip(columns, row))

async def update_city_forecast(city_name: str, latitude: float, longitude: float):
    hourly_data = await fetch_daily_forecast(latitude, longitude)
    save_forecast(city_name, hourly_data)
    print(f"Forecast for {city_name} updated")


async def update_all_forecasts():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, latitude, longitude FROM cities")
        cities = cursor.fetchall()
    tasks = []
    for city_name, lat, lon in cities:
        tasks.append(update_city_forecast(city_name, lat, lon))
    if tasks:
        await asyncio.gather(*tasks)


async def scheduler():
    while True:
        print(f"{datetime.now()}: Updating forecasts for all cities...")
        await update_all_forecasts()
        await asyncio.sleep(15 * 60)


@app.on_event("startup")
async def startup_event():
    init_db()
    asyncio.create_task(scheduler())

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)