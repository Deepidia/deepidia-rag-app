import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


@app.get("/")
async def root():
    return {"message": "API Is Active!"}


@app.get("/{path:path}")  # Catch-all route for any unmatched paths
async def not_found(path: str):
    return JSONResponse(content={"message": "API Not Found!"}, status_code=404)
