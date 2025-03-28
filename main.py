import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from routers import patients, pathways, templates, notifications, insights, care_teams, assignments

# Create FastAPI app
app = FastAPI(
    title="Healthcare Pathway API",
    description="API for managing healthcare care pathways",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(pathways.router, prefix="/api/pathways", tags=["pathways"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
app.include_router(care_teams.router, prefix="/api/care-teams", tags=["care-teams"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["assignments"])

# Health check endpoint
@app.get("/api", tags=["health"])
async def health_check():
    return {
        "status": "ok",
        "service": "healthcare-pathway-system",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

