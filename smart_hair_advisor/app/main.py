from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chatbot

# Initialize FastAPI app
app = FastAPI(
    title="Smart Hair Advisor",
    description="AI-powered chatbot that recommends Gliss hair products based on user profile and hair image.",
    version="1.0.0"
)

# Allow frontend or Streamlit to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to Smart Hair Advisor API 🚀"}

app.include_router(chatbot.router)