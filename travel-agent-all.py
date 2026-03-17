import json
import vertexai
from vertexai.generative_models import GenerativeModel

# ----------------------------
# Vertex AI setup
# ----------------------------
PROJECT_ID = "companionai-453821"
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)

model = GenerativeModel("gemini-2.0-flash")


# ----------------------------
# User memory (simple version)
# ----------------------------
user_profile = {
    "preferred_airline": "Air Canada",
    "max_budget": 2000,
    "seat_preference": "window"
}


# ----------------------------
# Mock tools
# ----------------------------
def search_flights(origin, destination):

    return [
        {"flight": "AC123", "airline": "Air Canada", "price": 450, "duration": 5},
        {"flight": "WS456", "airline": "WestJet", "price": 400, "duration": 6},
        {"flight": "UA789", "airline": "United", "price": 520, "duration": 5.5},
    ]


def search_hotels(city):

    return [
        {"hotel": "Grand Vancouver", "price": 150},
        {"hotel": "Downtown Inn", "price": 120},
        {"hotel": "Budget Stay", "price": 90},
    ]


# ----------------------------
# Ranking engine
# ----------------------------
def rank_options(flights, hotels):

    results = []

    for f in flights:
        for h in hotels:

            score = 0

            score += 1000 / f["price"]
            score += 500 / h["price"]

            if f["airline"] == user_profile["preferred_airline"]:
                score += 10

            results.append(
                {
                    "flight": f,
                    "hotel": h,
                    "score": score
                }
            )

    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:3]


# ----------------------------
# Agent planner
# ----------------------------
import json
import re

def extract_trip(prompt):

    planning_prompt = f"""
You are a travel planner.

Extract the trip details from the request.

Return ONLY valid JSON.
No explanation.
No markdown.

Example format:

{{
"origin": "Toronto",
"destination": "Iceland",
"days": 5
}}

User request:
{prompt}
"""

    response = model.generate_content(planning_prompt)

    text = response.text.strip()

    # Remove markdown if present
    text = re.sub(r"```json|```", "", text).strip()

    try:
        return json.loads(text)

    except json.JSONDecodeError:

        print("⚠️ JSON parse failed, using fallback")

        return {
            "origin": "Toronto",
            "destination": prompt,
            "days": 5
        }

# ----------------------------
# Final explanation
# ----------------------------
def explain_trip(options, days, origin, destination):

    prompt = f"""
You are a helpful travel agent.

Trip: {days} days
From: {origin}
To: {destination}

Top options:
{options}

Explain the best itinerary clearly for the traveler.
"""

    response = model.generate_content(prompt)

    return response.text

def run_agent(user_prompt):

    conversation = f"""
You are an AI travel planner.

You can use these tools:

search_flights(origin, destination)
search_hotels(city)

Respond using this format:

Thought: reasoning
Action: tool_name(arguments)
Observation: result
...
Final Answer: explanation for the user

User request: {user_prompt}
"""

    while True:

        print("\n--- AGENT THINKING ---")

        response = model.generate_content(conversation)

        text = response.text
        print(text)

        # Stop if finished
        if "Final Answer:" in text:
            return text.split("Final Answer:")[1].strip()

        # Detect tool call
        if "search_flights" in text:

            origin = "Toronto"
            destination = user_prompt

            result = search_flights(origin, destination)

            conversation += f"\nObservation: {result}\n"

        elif "search_hotels" in text:

            result = search_hotels(user_prompt)

            conversation += f"\nObservation: {result}\n"

        else:

            return text
        

while True:

    user_input = input("\nWhere would you like to travel? (or 'exit'): ")

    if user_input == "exit":
        break

    answer = run_agent(user_input)

    print("\nAgent response:\n")
    print(answer)