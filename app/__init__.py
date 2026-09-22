from flask import Flask, jsonify, render_template, request
from sqlalchemy import inspect

from .config import Config
from .extensions import db, jwt, limiter


def _repair_missing_columns(app):
    """Apply small additive schema repairs for deployments that predate model changes.

    db.create_all() does not alter existing tables. Render deployments can therefore
    have a healthy database connection but an older table schema, which causes
    Flask routes to fail with HTTP 500 when SQLAlchemy selects a newly-added column.
    This repair only adds columns that are missing; it never drops or changes data.
    """
    inspector = inspect(db.engine)
    from . import models

    model_classes = [
        models.User,
        models.Pet,
        models.MedicalRecord,
        models.Vaccination,
        models.Medication,
        models.Appointment,
        models.Reminder,
        models.Notification,
        models.WeightRecord,
        models.PreventiveCare,
        models.MedicalDocument,
        models.AuditLog,
    ]

    for model in model_classes:
        table_name = model.__tablename__
        if not inspector.has_table(table_name):
            continue

        existing = {c["name"] for c in inspector.get_columns(table_name)}
        for column in model.__table__.columns:
            if column.name in existing:
                continue

            # Existing Render databases may predate a required column. A plain
            # ADD COLUMN without a database default fails when rows already exist.
            # Only use explicit, known-safe defaults here; foreign keys and business
            # data fields are intentionally left for real migrations.
            safe_defaults = {
                ("users", "role"): "'owner'",
                ("users", "is_active"): "TRUE",
                ("users", "created_at"): "CURRENT_TIMESTAMP",
                ("pets", "created_at"): "CURRENT_TIMESTAMP",
                ("medical_records", "record_date"): "CURRENT_DATE",
                ("medical_records", "created_at"): "CURRENT_TIMESTAMP",
                ("vaccinations", "given_date"): "CURRENT_DATE",
                ("vaccinations", "created_at"): "CURRENT_TIMESTAMP",
                ("medications", "start_date"): "CURRENT_DATE",
                ("medications", "active"): "TRUE",
                ("medications", "created_at"): "CURRENT_TIMESTAMP",
                ("appointments", "appointment_date"): "CURRENT_DATE",
                ("appointments", "status"): "'upcoming'",
                ("appointments", "created_at"): "CURRENT_TIMESTAMP",
                ("reminders", "reminder_type"): "'custom'",
                ("reminders", "due_date"): "CURRENT_DATE",
                ("reminders", "status"): "'upcoming'",
                ("reminders", "created_at"): "CURRENT_TIMESTAMP",
                ("notifications", "channel"): "'in_app'",
                ("notifications", "status"): "'pending'",
                ("notifications", "is_read"): "FALSE",
                ("notifications", "created_at"): "CURRENT_TIMESTAMP",
                ("weight_records", "recorded_on"): "CURRENT_DATE",
                ("preventive_care", "performed_on"): "CURRENT_DATE",
            }
            default_sql = safe_defaults.get((table_name, column.name))
            if not column.nullable and column.default is None and column.server_default is None and not default_sql:
                app.logger.warning(
                    "Schema repair skipped required column %s.%s; run a real migration.",
                    table_name,
                    column.name,
                )
                continue

            column_type = column.type.compile(dialect=db.engine.dialect)
            default_clause = f" DEFAULT {default_sql}" if default_sql else ""
            sql = db.text(
                f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {column_type}{default_clause}'
            )
            try:
                db.session.execute(sql)
                db.session.commit()
                app.logger.warning(
                    "Schema repair added missing column %s.%s",
                    table_name,
                    column.name,
                )
                inspector = inspect(db.engine)
                existing.add(column.name)
            except Exception:
                db.session.rollback()
                app.logger.exception(
                    "Schema repair failed for %s.%s",
                    table_name,
                    column.name,
                )
                raise


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)

    from .routes import web, api
    app.register_blueprint(web)
    app.register_blueprint(api, url_prefix="/api")

    @app.get("/health")
    def health():
        try:
            db.session.execute(db.text("SELECT 1"))
            return {"status": "healthy", "database": "ok"}
        except Exception as exc:
            app.logger.exception("Health check failed")
            return {
                "status": "degraded",
                "database": "error",
                "message": str(exc),
            }, 503

    @app.errorhandler(500)
    def internal_error(exc):
        # Always log the real traceback in Render logs. API callers receive
        # JSON so the frontend can show the actual safe error message instead
        # of trying to parse an HTML 500 page.
        app.logger.exception("Unhandled application error")
        db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify({
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "The server could not complete that request. Please try again.",
                },
            }), 500
        return render_template(
            "error.html",
            error_id=getattr(exc, "original_exception", None) or exc,
        ), 500

    with app.app_context():
        from . import models

        db.create_all()

        # Keep existing Render databases compatible with newer model fields.
        _repair_missing_columns(app)

        from .services.seed import ensure_demo_admin, seed_demo_data
        admin = ensure_demo_admin()
        seed_demo_data(admin)

    return app
