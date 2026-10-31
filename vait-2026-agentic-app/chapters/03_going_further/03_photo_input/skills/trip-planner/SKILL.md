---
name: trip-planner
description: Plans a trip step by step. Gathers where, who, when and how long, checks dates, weather, places and food with tools, then builds a day-by-day plan. Use whenever someone asks to plan a trip, a day out, or an itinerary.
allowed-tools: current_time get_weather find_attractions find_restaurants
---

# Trip planner

## 1. Gather the essentials

Before planning, make sure you know:

| What | Details |
|---|---|
| Where | destination(s), in order, and where the travellers start from |
| Who | how many people, ages (children, older adults), and any special needs: diet, mobility, health |
| When | the start date |
| How long | the number of days |

- Ask only for what is still missing, at most three short questions in one message, then wait for the answer.
- Never ask again for something the user already told you.
- Work out dates like "next Friday" with `current_time`. Never guess today's date.

## 2. Check the facts

- `get_weather` for every day of the trip, with real dates.
- `find_attractions` per city; `find_restaurants` per city for meals.
- If the travellers have dietary or mobility needs, load the matching skill (`dietary-needs`, `accessible-travel`) and follow it.

## 3. Build the plan

- One section per day: city, weather, 2–4 stops, lunch and dinner.
- Rain: choose indoor stops.
- Keep travel between stops short; put the most important stop first.

## 4. Present it

- Start with one line: who, where, when, how long.
- Then the days as short bullets.
- End with any assumptions you made, in one line.
