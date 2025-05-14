import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from rag import ViralTopicGenerator

app = FastAPI()

# CORS middleware setup to allow cross-origin requests
origins = [
    "http://localhost:3000",  # Update with your frontend URL if needed
    "https://yourfrontend.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows only the specified origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)


class TopicRequest(BaseModel):
    model_type: str = "openai"  # Default
    category: str = "Technology"
    scope: str = "Trending Now"
    keyword: Optional[str] = None
    num_ideas: int = 5


@app.get("/")
async def root():
    return {"message": "API Is Active!"}


@app.post("/api/v1/generate_viral_ideas")
async def get_topics(request: TopicRequest):
    try:
        generator = ViralTopicGenerator(model_type=request.model_type)
        ideas = generator.generate_viral_ideas(
            topic_type=request.category,
            scope=request.scope,
            keyword=request.keyword,
            num_ideas=request.num_ideas)

        return JSONResponse(
            content={
                "model": request.model_type,
                "category": request.category,
                "scope": request.scope,
                "keyword": request.keyword,  # Will be None if not provided
                "ideas": ideas,
            },
            status_code=200,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/{path:path}")  # Catch-all route for any unmatched paths
async def not_found(path: str):
    return JSONResponse(content={"message": "API Not Found!"}, status_code=404)
