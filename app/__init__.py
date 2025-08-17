from flask import Flask
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from .config import Config

# 1.  create engine & sessionmaker at import time
engine = create_async_engine(Config.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# 2.  factory only registers blueprints
def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    from .routes import clients, cash_runs, home
    app.register_blueprint(clients.bp)
    app.register_blueprint(cash_runs.bp)
    app.register_blueprint(home.bp)

    return app