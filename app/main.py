from fastapi import FastAPI

from app.api.routes import router
from app.db.database import init_db

app = FastAPI(title="Matrix Maintainer", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


app.include_router(router)
