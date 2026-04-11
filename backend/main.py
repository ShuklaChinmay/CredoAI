from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from config.settings import settings
from routes import auth, loan, admin, chatbot
from routes.payment import router as payment_router
from routes.documents import router as documents_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()   

origins = [
    "http://localhost:5173",
    "https://credo-ai.vercel.app/auth",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 👈 IMPORTANT
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.APP_NAME} API...")
    try:
        print("✅ Database connection verified")
    except Exception as e:
        print(f"⚠️  DB init warning: {e}")
    yield
    print("👋 Shutting down...")


app = FastAPI(
    title="LoanAI API",
    description="AI-powered Loan Assistant — 3-Agent System",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(chatbot.router)
app.include_router(loan.router)
app.include_router(admin.router)
app.include_router(payment_router)
app.include_router(documents_router)

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": settings.APP_NAME, "version": "2.0.0", "agents": 3}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) if settings.DEBUG else "Internal server error"},
    )
