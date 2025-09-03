from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.core.session import async_session, engine
from app.schemas.user_schema import UserCreate
from app.services.user_service import get_user_by_email, create_user

from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.api.tasks import router as task_router  


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        redoc_url=None,
    )

    @app.get("/", include_in_schema=False)
    async def root_redirect():
        return RedirectResponse(url="/auth/login")

    app.include_router(auth_router, prefix="/auth", tags=["Autenticación"])
    app.include_router(user_router, prefix="/users", tags=["Usuarios"])
    app.include_router(task_router, prefix="/tasks", tags=["Tareas"])  

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SessionMiddleware, secret_key=settings.DB_SECRET_KEY)

    
    return app


app = create_app()


@app.on_event("startup")
async def startup_event():
    async with async_session() as db:
        admin_email = "admin@task.com"
        existing_user = await get_user_by_email(db, admin_email)
        if not existing_user:
            admin_user = UserCreate(
                name_complete="Administrador",
                email=admin_email,
                password="admin",
                role="Admin",
            )
            await create_user(db, admin_user)


@app.on_event("shutdown")
async def shutdown_event():
    await engine.dispose()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
