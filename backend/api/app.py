import uvicorn
from routes import app

uvicorn.run(app, host="0.0.0.0", port=8000)