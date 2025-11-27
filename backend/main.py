import uvicorn
from config.settings import HOST, PORT

if __name__ == "__main__":
    uvicorn.run(
        "api.routes:app",
        host=HOST,
        port=PORT,
        reload=True
    )