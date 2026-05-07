import requests

SKILL_NAME = "weather_checker"
SKILL_DESCRIPTION = "Fetches simple current weather text for a city via wttr.in."


def execute(args: dict) -> str:
    # Read city from args and use a sane default so the skill never crashes.
    city = args.get("city", "London")

    # wttr.in returns a compact weather sentence with format=3.
    url = f"https://wttr.in/{city}?format=3"

    # Keep timeout short so the agent loop remains responsive.
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    # Return human-friendly weather text for the assistant to speak.
    return f"Weather for {city}: {response.text.strip()}"
