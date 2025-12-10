"""Weather tools using Open-Meteo API (free, no API key required).

Provides weather information for voice agent.
"""

import httpx
from livekit.agents import function_tool, RunContext

# Weather code descriptions
WEATHER_CODES = {
    0: "ясно",
    1: "преимущественно ясно",
    2: "переменная облачность",
    3: "пасмурно",
    45: "туман",
    48: "изморозь",
    51: "лёгкая морось",
    53: "морось",
    55: "сильная морось",
    61: "небольшой дождь",
    63: "дождь",
    65: "сильный дождь",
    71: "небольшой снег",
    73: "снег",
    75: "сильный снег",
    80: "ливень",
    81: "сильный ливень",
    95: "гроза",
    96: "гроза с градом",
}


def _pluralize_degrees(n: int) -> str:
    """Return correct Russian plural form for 'градус'."""
    if 11 <= n % 100 <= 19:
        return "градусов"
    last_digit = n % 10
    if last_digit == 1:
        return "градус"
    elif 2 <= last_digit <= 4:
        return "градуса"
    else:
        return "градусов"


def _pluralize_kmh(n: int) -> str:
    """Return correct Russian plural form for 'километр в час'."""
    if 11 <= n % 100 <= 19:
        return "километров в час"
    last_digit = n % 10
    if last_digit == 1:
        return "километр в час"
    elif 2 <= last_digit <= 4:
        return "километра в час"
    else:
        return "километров в час"


async def _geocode_city(city: str) -> tuple[float, float, str] | None:
    """Get coordinates for a city name using Open-Meteo geocoding."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "ru"},
            timeout=10,
        )
        data = resp.json()
        if not data.get("results"):
            return None
        result = data["results"][0]
        return result["latitude"], result["longitude"], result.get("name", city)


@function_tool
async def get_weather(context: RunContext, city: str) -> str:
    """Получить текущую погоду для города.
    
    Args:
        city: Название города (на русском или английском)
    
    Returns:
        Описание текущей погоды
    """
    # Geocode city
    coords = await _geocode_city(city)
    if not coords:
        return f"Не удалось найти город: {city}"
    
    lat, lon, city_name = coords
    
    # Get weather
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
            timeout=10,
        )
        data = resp.json()
    
    current = data.get("current", {})
    temp = current.get("temperature_2m", 0)
    code = current.get("weather_code", 0)
    wind = current.get("wind_speed_10m", 0)
    
    weather_desc = WEATHER_CODES.get(code, "неизвестно")
    
    # Format temperature for speech (e.g., "минус 5 градусов")
    temp_int = int(round(temp))
    if temp_int < 0:
        temp_speech = f"минус {abs(temp_int)} {_pluralize_degrees(abs(temp_int))}"
    elif temp_int == 0:
        temp_speech = "ноль градусов"
    else:
        temp_speech = f"{temp_int} {_pluralize_degrees(temp_int)}"
    
    # Format wind for speech
    wind_int = int(round(wind))
    wind_speech = f"{wind_int} {_pluralize_kmh(wind_int)}"
    
    return f"Погода в городе {city_name}: {temp_speech}, {weather_desc}, ветер {wind_speech}"


# Export tools list
TOOLS = [get_weather]
