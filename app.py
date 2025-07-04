import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
from rag import ViralTopicGenerator
from rag.agent_content_creation.content_bank_postgres import (
    generate_ideas_and_store_postgres, 
    get_user_ideas_from_postgres, 
    export_ideas_to_csv,
    export_ideas_to_excel,
    export_ideas_to_json,
)

app = FastAPI()

# CORS middleware setup to allow cross-origin requests
origins = [
    "http://localhost:3000",  # Update with your frontend URL if needed
    "https://yourfrontend.com",
    "https://api.deepidia.com",
    "https://deepidia.com",
    "https://deepidia-web.vercel.app",
	"https://deepidia-web.vercel.app/",
	"https://deepidia-web.vercel.app/idea/generate",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows only the specified origins
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


class TopicStoreRequest(TopicRequest):
    username: str  # For the old file-based storage


class TopicStorePostgresRequest(TopicRequest):
    name: str  # For PostgreSQL storage
    export_formats: Optional[List[str]] = ["csv"]  # ["csv", "json", "both", "none"]


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

    
@app.post("/api/v1/content_creation")
async def get_topics_and_store_postgres(request: TopicStorePostgresRequest):
    try:
        # Generate ideas and store in PostgreSQL with export
        ideas, storage_message, export_info = generate_ideas_and_store_postgres(
            request.model_type,
            request.category,
            request.scope,
            request.keyword,
            request.num_ideas,
            request.name,
            request.export_formats
        )
        
        response_content = {
            "model": request.model_type,
            "category": request.category,
            "scope": request.scope,
            "keyword": request.keyword,
            "ideas": ideas,
            "storage_message": storage_message,
            "name": request.name,
            "export_formats": request.export_formats,
            "export_info": export_info,
        }
        
        return JSONResponse(
            content=response_content,
            status_code=200,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/download/{name}")
async def download_user_file(name: str, format: str = "csv", limit: int = 100):
    """
    Download user's ideas as CSV, Excel, or JSON file
    
    Args:
        name: The user name
        format: Download format - "csv", "excel", or "json"
        limit: Maximum number of ideas to include
    """
    try:
        # Validate format parameter
        if format.lower() not in ["csv", "excel", "json"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid format. Must be 'csv', 'excel', or 'json'"
            )
        
        # Get user's ideas from database
        ideas = get_user_ideas_from_postgres(name, limit)
        
        if not ideas:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "No ideas found for this user yet",
                    "name": name,
                    "suggestions": [
                        "Generate your first ideas using POST /api/v1/content_creation",
                        "Try different categories like Technology, Business, or Lifestyle",
                        "Use trending keywords to get more relevant ideas"
                    ],
                    "example_request": {
                        "model_type": "gemini",
                        "category": "Technology",
                        "scope": "Trending Now",
                        "keyword": "AI",
                        "num_ideas": 5,
                        "name": name,
                        "export_formats": [format.lower()]
                    },
                    "available_formats": ["csv", "excel", "json"],
                    "download_endpoint": f"/api/v1/download/{name}?format={{format}}&limit={{limit}}"
                }
            )
        
        # Convert to the format expected by export function
        formatted_ideas = []
        for idea in ideas:
            formatted_ideas.append({
                "title": idea["title"],
                "description": idea["description"]
            })
        
        format_lower = format.lower()
        
        if format_lower == "csv":
            # Export to CSV
            csv_filepath = export_ideas_to_csv(
                formatted_ideas, 
                name, 
                ideas[0]["model_type"], 
                ideas[0]["category"], 
                ideas[0]["scope"], 
                ideas[0]["keyword"]
            )
            
            return FileResponse(
                path=csv_filepath,
                filename=f"{name}_ideas.csv",
                media_type="text/csv"
            )
            
        elif format_lower == "excel":
            # Export to Excel
            excel_filepath = export_ideas_to_excel(
                formatted_ideas, 
                name, 
                ideas[0]["model_type"], 
                ideas[0]["category"], 
                ideas[0]["scope"], 
                ideas[0]["keyword"]
            )
            
            return FileResponse(
                path=excel_filepath,
                filename=f"{name}_ideas.xlsx",
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        elif format_lower == "json":
            # Export to JSON
            json_filepath = export_ideas_to_json(
                formatted_ideas, 
                name, 
                ideas[0]["model_type"], 
                ideas[0]["category"], 
                ideas[0]["scope"], 
                ideas[0]["keyword"]
            )
            
            return FileResponse(
                path=json_filepath,
                filename=f"{name}_ideas.json",
                media_type="application/json"
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/export_formats")
async def get_available_export_formats():
    """
    Get information about available export formats
    """
    return {
        "available_formats": {
            "csv": {
                "description": "Comma-separated values file",
                "benefits": ["No quota limits", "Works offline", "Import to any spreadsheet", "Appends to existing file"],
                "download_endpoint": "/api/v1/download/{name}?format=csv",
                "recommended": True
            },
            "excel": {
                "description": "Microsoft Excel file (.xlsx)",
                "benefits": ["Native Excel format", "Preserves formatting", "Easy to work with", "Appends to existing file"],
                "download_endpoint": "/api/v1/download/{name}?format=excel",
                "recommended": True
            },
            "json": {
                "description": "JavaScript Object Notation file",
                "benefits": ["Structured data", "Easy to parse", "Good for APIs", "Appends to existing file"],
                "download_endpoint": "/api/v1/download/{name}?format=json",
                "recommended": True
            }
        },
        "usage_examples": {
            "csv_only": {"export_formats": ["csv"]},
            "excel_only": {"export_formats": ["excel"]},
            "json_only": {"export_formats": ["json"]},
            "all_formats": {"export_formats": ["csv", "excel", "json"]},
            "no_export": {"export_formats": ["none"]}
        },
        "download_endpoints": {
            "csv": "/api/v1/download/{name}?format=csv",
            "excel": "/api/v1/download/{name}?format=excel", 
            "json": "/api/v1/download/{name}?format=json"
        },
        "note": "All exports append to existing files, maintaining a single consolidated file per user"
    }


@app.get("/{path:path}")  # Catch-all route for any unmatched paths
async def not_found(path: str):
    return JSONResponse(content={"message": "API Not Found!"}, status_code=404)
