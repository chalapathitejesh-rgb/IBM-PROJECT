from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api import auth, deepfake, voice, email, url, network, fusion, forensics, cases
from .db import database, models
from .core.security import get_password_hash
from sqlalchemy.orm import Session

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.on_event("startup")
def on_startup():
    db: Session = database.SessionLocal()
    try:
        # Check if admin role exists
        admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
        if not admin_role:
            admin_role = models.Role(name="admin")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            
        # Check if admin exists
        admin = db.query(models.User).filter(models.User.email == "admin@deepsheild.com").first()
        if not admin:
            # Create default admin user
            admin = models.User(
                email="admin@deepsheild.com",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                role_id=admin_role.id
            )
            db.add(admin)
            db.commit()
            print("Default admin user created: admin@deepsheild.com / admin123")
    finally:
        db.close()

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(cases.router, prefix=f"{settings.API_V1_STR}/cases", tags=["cases"])
app.include_router(deepfake.router, prefix=f"{settings.API_V1_STR}/deepfake", tags=["deepfake"])
app.include_router(voice.router, prefix=f"{settings.API_V1_STR}/voice", tags=["voice"])
app.include_router(email.router, prefix=f"{settings.API_V1_STR}/email", tags=["email"])
app.include_router(url.router, prefix=f"{settings.API_V1_STR}/url", tags=["url"])
app.include_router(network.router, prefix=f"{settings.API_V1_STR}/network", tags=["network"])
app.include_router(fusion.router, prefix=f"{settings.API_V1_STR}/fusion", tags=["fusion"])
app.include_router(forensics.router, prefix=f"{settings.API_V1_STR}/forensics", tags=["forensics"])

@app.get("/")
def read_root():
    return {"message": "Welcome to HTCS API Gateway"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
