"""Mock data so the demo is repeatable and needs no API keys besides the LLM."""

FORECASTS = {
    "Kyoto": {"temp_c": 18, "conditions": "heavy rain all day"},
    "Tokyo": {"temp_c": 21, "conditions": "sunny"},
    "Osaka": {"temp_c": 20, "conditions": "cloudy"},
}

ATTRACTIONS = {
    "Kyoto": [
        {"name": "Fushimi Inari Shrine", "photo": "fushimi-inari", "indoor": False, "step_free": False},
        {"name": "Arashiyama Bamboo Grove", "photo": "arashiyama-bamboo", "indoor": False, "step_free": True},
        {"name": "Kinkaku-ji (Golden Pavilion)", "photo": "kinkaku-ji", "indoor": False, "step_free": True},
        {"name": "Nishiki Market (covered arcade)", "photo": "nishiki-market", "indoor": True, "step_free": True},
        {"name": "Kyoto Railway Museum", "photo": "kyoto-railway-museum", "indoor": True, "step_free": True},
        {"name": "Tea ceremony at Camellia", "photo": "tea-ceremony", "indoor": True, "step_free": False},
    ],
    "Tokyo": [
        {"name": "Senso-ji Temple", "photo": "senso-ji", "indoor": False, "step_free": True},
        {"name": "Meiji Shrine", "photo": "meiji-shrine", "indoor": False, "step_free": True},
        {"name": "teamLab Planets", "indoor": True, "step_free": True},
        {"name": "Tsukiji Outer Market", "photo": "tsukiji-outer-market", "indoor": False, "step_free": True},
    ],
}

FLIGHTS = [
    {"flight": "VN300", "from": "Ho Chi Minh City", "to": "Tokyo (Narita)", "depart": "Fri 00:05", "arrive": "Fri 07:45", "price_usd": 420},
    {"flight": "JL750", "from": "Ho Chi Minh City", "to": "Tokyo (Haneda)", "depart": "Fri 08:30", "arrive": "Fri 16:00", "price_usd": 510},
    {"flight": "NH832", "from": "Ho Chi Minh City", "to": "Tokyo (Haneda)", "depart": "Thu 22:40", "arrive": "Fri 06:30", "price_usd": 480},
]

HOTELS = {
    "Tokyo": [
        {"name": "Hotel Gracery Shinjuku", "price_usd": 180, "step_free_room": True},
        {"name": "Asakusa Ryokan Sawanoya", "price_usd": 120, "step_free_room": False},
    ],
    "Kyoto": [
        {"name": "Hotel Granvia Kyoto (at Kyoto Station)", "price_usd": 230, "step_free_room": True},
        {"name": "Gion Machiya Inn", "price_usd": 160, "step_free_room": False},
    ],
}

RESTAURANTS = {
    "Kyoto": [
        {"name": "Shigetsu (inside Tenryu-ji, Arashiyama)", "cuisine": "shojin ryori (Buddhist temple food)",
         "diets": ["vegan", "vegetarian"], "step_free": False, "note": "tatami seating; ask for chairs"},
        {"name": "Ain Soph. Journey", "cuisine": "vegan cafe", "diets": ["vegan", "vegetarian"], "step_free": True},
        {"name": "Mumokuteki Cafe", "cuisine": "vegetarian cafe, near Nishiki Market", "diets": ["vegetarian"],
         "step_free": True, "note": "elevator"},
        {"name": "Ichiran Kyoto", "cuisine": "tonkotsu (pork) ramen", "diets": [], "step_free": True},
    ],
    "Tokyo": [
        {"name": "T's TanTan (Tokyo Station, inside the gates)", "cuisine": "vegan ramen", "diets": ["vegan", "vegetarian"],
         "step_free": True},
        {"name": "Ain Soph. Ginza", "cuisine": "vegan", "diets": ["vegan", "vegetarian"], "step_free": True},
        {"name": "Tsukiji Sushiko", "cuisine": "sushi", "diets": [], "step_free": True},
    ],
}
