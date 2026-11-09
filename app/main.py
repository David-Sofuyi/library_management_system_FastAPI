import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.database.connection import init_db
from app.routes.book_routes import router as book_router

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield


app = FastAPI(
    title="Library Management System API",
    description="A FastAPI-based Library Management System with full frontend UI & SQLite ORM.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register static files directory
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Register route modules
app.include_router(book_router)


@app.get("/", tags=["Frontend"])
def serve_frontend():
    """Serves the Library Management interactive Single Page Dashboard."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "message": "Welcome to the Library Management System API",
        "documentation": "/docs",
        "redoc": "/redoc",
        "status": "healthy",
    }


@app.get("/health", tags=["General"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
