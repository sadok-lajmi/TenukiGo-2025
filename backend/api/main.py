import uvicorn
from routes import app
from config.settings import HOST, PORT

uvicorn.run(app, host=HOST, port=PORT)