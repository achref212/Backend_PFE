from flask import Flask

def create_app():
    app = Flask(__name__)

    from app.routes.scraping_route import scraping_bp
    app.register_blueprint(scraping_bp)

    return app
