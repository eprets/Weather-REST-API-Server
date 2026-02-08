# Weather REST API Server

HTTP-сервер на Python для предоставления прогноза погоды.  
Использует **FastAPI**, хранение данных в **SQLite**, асинхронные запросы к Open-Meteo.  

---
## Запуск

1. Установить зависимости:

```bash
pip install fastapi uvicorn httpx
```
2. Запустить сервер:

```bash
python3 script.py
```
3. Сервер доступен по адресу:
http://127.0.0.1:8000
4. Swagger-документация: 
http://127.0.0.1:8000/docs

Примечание: SQLite база создаётся автоматически при первом запуске сервера — установка или настройка SQLite на машине не требуется.
---
## Методы API

1. Текущая погода по координатам

GET /current-weather

Параметры:

latitude — широта (float, обязательный)

longitude — долгота (float, обязательный)
```bash
GET /current-weather?latitude=52.52&longitude=13.41
# Ответ:
{
  "temperature": 5.3,
  "wind_speed": 12.1,
  "pressure": 1014.2
}
```
2. Добавление города

POST /add-city

Параметры:

name — название города (str, обязательный)

latitude — широта (float, обязательный)

longitude — долгота (float, обязательный)
```bash
POST /add-city?name=Berlin&latitude=52.52&longitude=13.41
# Ответ:
{
  "message": "City Berlin added and forecast saved"
}
```
3. Список городов
GET /cities
```bash
GET /cities
# Ответ:
["Berlin", "Paris", "Moscow"]
```
4. Погода города на указанное время с выбором параметров

GET /weather

Параметры:

city — название города (str, обязательный)

time — время в формате HH:MM, например 14:00 (обязательный)

fields — параметры через запятую: temperature,humidity,wind_speed,precipitation,pressure (обязательный)

```bash
GET /weather?city=Berlin&time=14:00&fields=temperature,wind_speed
# Ответ:
{
  "temperature": 6.2,
  "wind_speed": 10.3
}
```
5. Автообновление прогнозов

Прогнозы обновляются каждые 15 минут автоматически.

В консоли выводится:
```bash
2026-02-05 12:00:00: Updating forecasts for all cities...
Forecast for Berlin updated
Forecast for Paris updated
```
6. Хранение данных

SQLite база weather.db создаётся автоматически.

Таблицы:

cities — города и координаты

forecasts — почасовой прогноз для каждого города

## Дополнительные задания
 юнит-тесты на методы API
 
Запуск:
```bash
pytest