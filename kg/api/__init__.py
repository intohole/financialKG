from .router import router

def include_routers(app):
    app.include_router(router, prefix="/api/v1")
