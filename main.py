from fastapi import FastAPI
import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = "companionai-453821"
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)

model = GenerativeModel("gemini-2.0-flash")

app = FastAPI()

def travel_agent(user_prompt):

    response = model.generate_content(
        f"You are a travel assistant. Plan a trip for: {user_prompt}"
    )

    return response.text


@app.get("/travel")
def travel(query: str):

    result = travel_agent(query)

    return {"result": result}