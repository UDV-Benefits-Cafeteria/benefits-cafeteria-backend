import uvicorn

from src.application import create_application

app = create_application()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
