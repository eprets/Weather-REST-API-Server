from httpx import AsyncClient, ASGITransport
from script import app
import pytest


def get_client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_root():
    async with get_client() as ac:
        r = await ac.get("/")
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_current_weather():
    async with get_client() as ac:
        r = await ac.get(
            "/current-weather?latitude=52.52&longitude=13.41"
        )
        assert r.status_code == 200
        data = r.json()
        assert "temperature" in data
        assert "wind_speed" in data
        assert "pressure" in data


@pytest.mark.asyncio
async def test_add_city():
    async with get_client() as ac:
        r = await ac.post(
            "/add-city?name=Berlin&latitude=52.52&longitude=13.41"
        )
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_get_cities():
    async with get_client() as ac:
        r = await ac.get("/cities")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_weather_by_time():
    async with get_client() as ac:
        r = await ac.get(
            "/weather?city=Berlin&time=14:00&fields=temperature,wind_speed"
        )
        assert r.status_code == 200
        data = r.json()
        assert "temperature" in data