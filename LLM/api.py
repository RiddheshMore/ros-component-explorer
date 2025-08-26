"""
LLM-Enhanced API endpoints for the ROS Component Explorer.

Provides REST API endpoints for natural language querying of ROS components
using the LLM search engine.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LLM.llm_search_engine import LLMSearchEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ROS Component Explorer LLM API",
    description="Natural language interface for querying ROS components",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global LLM search engine instance
llm_engine: Optional[LLMSearchEngine] = None

class NLQueryRequest(BaseModel):
    """Request model for natural language queries."""
    query: str
    max_results: Optional[int] = 10
    include_metadata: Optional[bool] = True

class NLQueryResponse(BaseModel):
    """Response model for natural language queries."""
    query: str
    synthesized_response: str
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    requirements: Optional[Dict[str, Any]] = None
    search_params: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    message: str
    llm_engine_ready: bool

@app.on_event("startup")
async def startup_event():
    """Initialize the LLM search engine on startup."""
    global llm_engine
    try:
        ttl_file = "/home/ritz/Desktop/RnD/data/components.ttl"
        llm_engine = LLMSearchEngine(ttl_file)
        logger.info("LLM Search Engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LLM Search Engine: {e}")
        llm_engine = None

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if llm_engine else "unhealthy",
        message="LLM API is running" if llm_engine else "LLM engine not initialized",
        llm_engine_ready=llm_engine is not None
    )

@app.post("/api/v1/nlquery", response_model=NLQueryResponse)
async def natural_language_query(request: NLQueryRequest):
    """
    Process a natural language query and return structured results.
    
    This endpoint accepts natural language queries like:
    - "What is the best SLAM package for outdoor robots with 3D LiDAR?"
    - "I need navigation components for indoor environments"
    - "Recommend perception packages for object detection"
    """
    if not llm_engine:
        raise HTTPException(
            status_code=503, 
            detail="LLM search engine not available"
        )
    
    try:
        # Process the query
        result = llm_engine.process_natural_language_query(
            request.query, 
            max_results=request.max_results
        )
        
        # Prepare response
        response_data = {
            "query": result["query"],
            "synthesized_response": result["synthesized_response"],
            "results": result["results"],
            "metadata": result["metadata"]
        }
        
        # Include additional data if requested
        if request.include_metadata:
            response_data["requirements"] = result.get("requirements")
            response_data["search_params"] = result.get("search_params")
        
        return NLQueryResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error processing natural language query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@app.get("/api/v1/nlquery")
async def natural_language_query_get(
    q: str = Query(..., description="Natural language query"),
    max_results: int = Query(10, description="Maximum number of results"),
    include_metadata: bool = Query(True, description="Include metadata in response")
):
    """
    GET version of natural language query endpoint.
    
    Useful for simple queries via URL parameters.
    """
    request = NLQueryRequest(
        query=q,
        max_results=max_results,
        include_metadata=include_metadata
    )
    return await natural_language_query(request)

@app.get("/api/v1/examples")
async def get_example_queries():
    """
    Get example natural language queries that work well with the system.
    """
    return {
        "examples": [
            {
                "query": "What is the best SLAM package for a robot with a 3D LiDAR and an IMU in a large, outdoor environment?",
                "description": "Recommendation query with specific sensors and environment"
            },
            {
                "query": "I need a navigation stack for indoor environments with stereo cameras",
                "description": "Component search with environment and sensor constraints"
            },
            {
                "query": "Recommend a localization package for outdoor robots with GPS and wheel odometry",
                "description": "Localization-specific query with multiple sensor types"
            },
            {
                "query": "Find perception components for object detection using depth cameras",
                "description": "Category-specific search with sensor specification"
            },
            {
                "query": "What planning algorithms work well with 2D LiDAR in real-time?",
                "description": "Algorithm search with performance requirements"
            },
            {
                "query": "Compare SLAM packages for indoor robots",
                "description": "Comparison query for specific environment"
            },
            {
                "query": "Explain what move_base does in ROS navigation",
                "description": "Explanation query for specific component"
            }
        ]
    }

@app.get("/api/v1/categories")
async def get_supported_categories():
    """
    Get the list of supported component categories.
    """
    if not llm_engine:
        raise HTTPException(
            status_code=503,
            detail="LLM search engine not available"
        )
    
    categories = list(llm_engine.query_processor.category_keywords.keys())
    return {
        "categories": [
            {
                "name": cat.value,
                "display_name": cat.value.replace("_", " ").title(),
                "keywords": llm_engine.query_processor.category_keywords[cat]
            }
            for cat in categories
        ]
    }

@app.get("/api/v1/sensors")
async def get_supported_sensors():
    """
    Get the list of supported sensor types.
    """
    if not llm_engine:
        raise HTTPException(
            status_code=503,
            detail="LLM search engine not available"
        )
    
    sensors = list(llm_engine.query_processor.sensor_keywords.keys())
    return {
        "sensors": [
            {
                "name": sensor.value,
                "display_name": sensor.value.replace("_", " ").title(),
                "keywords": llm_engine.query_processor.sensor_keywords[sensor]
            }
            for sensor in sensors
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
