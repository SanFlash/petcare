from flask import Flask
from .config import Config
from .extensions import db, jwt, limiter

def create_app():
    app=Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app); jwt.init_app(app); limiter.init_app(app)
    from .routes import web, api
    app.register_blueprint(web); app.register_blueprint(api,url_prefix='/api')
    @app.get('/health')
    def health():
        try:
            db.session.execute(db.text('SELECT 1'))
            return {'status':'healthy','database':'ok'}
        except Exception as exc:
            app.logger.exception('Health check failed')
            return {'status':'degraded','database':'error','message':str(exc)},503
    with app.app_context():
        from . import models
        db.create_all()
        from .services.seed import ensure_demo_admin, seed_demo_data
        admin=ensure_demo_admin(); seed_demo_data(admin)
    return app
