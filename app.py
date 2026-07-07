from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from llm import ask_llm
import re


app = FastAPI(
    title="AI Solicitor Match API"
)

# -------------------------
# Load CSV
# -------------------------

df = pd.read_csv("solicitors.csv").fillna("")


# Clean data
df["postcode"] = (
    df["postcode"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)

df["authorisation_status"] = (
    df["authorisation_status"]
    .fillna("")
    .astype(str)
    .str.strip()
)

print(f"Loaded {len(df)} solicitors")


# -------------------------
# Request Model
# -------------------------

class Query(BaseModel):
    case_text: str
    postcode: str


# -------------------------
# Get postcode area
# Example:
# TS1 3EN -> TS
# NE12 4AB -> NE
# SW1A 1AA -> SW
# -------------------------

def get_postcode_area(postcode: str):

    postcode = postcode.strip().upper()

    match = re.match(r"^[A-Z]+", postcode)

    if match:
        return match.group()

    return ""

class ChatRequest(BaseModel):
    message: str



# -------------------------
# Root
# -------------------------

@app.get("/")
def home():
    return {
        "status": "API Running"
    }

@app.post("/chat")
def chat(request: ChatRequest):

    print("Received:", request.message)

    reply = ask_llm(request.message)

    print("LLM Reply:", repr(reply))

    return {
        "reply": reply
    }
# -------------------------
# Recommendation API
# -------------------------

@app.post("/recommend")
def recommend(query: Query):

    print("\n==========================")
    print("Incoming Request")
    print("==========================")

    print("Case:")
    print(query.case_text)

    print("User Postcode:")
    print(query.postcode)

    postcode_area = get_postcode_area(
        query.postcode
    )

    print("Postcode Area:")
    print(postcode_area)

    # Filter postcode
    filtered = df[
        df["postcode"].str.startswith(
            postcode_area,
            na=False
        )
    ]

    print(
        f"After postcode filter: {len(filtered)}"
    )

    # Filter Authorised
    filtered = filtered[
        filtered["authorisation_status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        == "yes"
    ]

    print(
        f"After authorisation filter: {len(filtered)}"
    )

    # Optional sort
    filtered = filtered.sort_values(
        by="practice_name"
    )

    print("==========================\n")

    return {
        "count": len(filtered),
        "recommendations": filtered.to_dict(
            orient="records"
        )
    }
