import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import init_db, engine, get_db
from app.graphql import schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables safely on startup
    init_db()
    yield


app = FastAPI(
    title="Release Checklist API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
raw_cors = os.getenv("CORS_ORIGINS", "*")
if raw_cors == "*":
    allow_origins = ["*"]
else:
    allow_origins = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_graphql_context(db: Session = Depends(get_db)):
    """Supply request-scoped database session directly to Strawberry resolvers."""
    return {"db": db}


graphql_app = GraphQLRouter(schema, context_getter=get_graphql_context)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
def health_check():
    """Health check endpoint verifying API and database connection."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "database": str(e)},
        )


@app.get("/")
def root():
    return {
        "name": "Release Checklist API",
        "graphql": "/graphql",
        "health": "/health",
        "docs": "/docs",
    }
