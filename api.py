from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.printer import router as printer_router
from routes.task import router as task_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(printer_router)
app.include_router(task_router)