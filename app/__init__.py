import logging
from flask import Flask, jsonify
from .utils.config import Settings
from .services.database_service import DatabaseManager
from .services.ml_service import MLPredictor
from .services.llm_service import LLMService
from .services.prompt_manager import PromptManager
from .services.ticket_service import TicketService
from .services.analytics_service import AnalyticsService
from .services.priority_queue import PriorityQueueManager
from .services.auth_service import AuthService
from .services.rate_limiter import RateLimiter
from .api.auth import auth_bp
from .api.tickets import tickets_bp
from .api.predictions import predictions_bp
from .api.ai import ai_bp
from .api.analytics import analytics_bp

def create_app(settings=None):
    settings = settings or Settings.from_env()
    app = Flask(__name__)
    app.config["SETTINGS"] = settings
    app.config["MAX_CONTENT_LENGTH"] = settings.max_content_length

    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    db = DatabaseManager(settings.database_path)
    db.initialize()
    ml = MLPredictor(settings.model_dir)
    prompts = PromptManager(settings.prompt_dir)
    llm = LLMService.from_settings(settings, prompts)
    queue = PriorityQueueManager()
    auth = AuthService(db, settings.secret_key, settings.token_ttl_seconds)
    limiter = RateLimiter(settings.rate_limit_per_minute)
    tickets = TicketService(db, ml, llm, prompts, queue)
    analytics = AnalyticsService(db)

    app.extensions["services"] = {
        "db": db, "ml": ml, "llm": llm, "prompts": prompts,
        "queue": queue, "tickets": tickets, "analytics": analytics, "auth": auth,
    }

    @app.before_request
    def enforce_rate_limit():
        from flask import request
        if request.path.startswith("/health"):
            return None
        key = request.headers.get("Authorization", "") or request.remote_addr or "anonymous"
        if not limiter.allow(key):
            from flask import abort
            abort(429)
        return None

    for bp in (auth_bp, tickets_bp, predictions_bp, ai_bp, analytics_bp):
        app.register_blueprint(bp, url_prefix="/api")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.errorhandler(400)
    def bad_request(_):
        return jsonify(error="Bad request"), 400

    @app.errorhandler(401)
    def unauthorized(_):
        return jsonify(error="Authentication required"), 401

    @app.errorhandler(403)
    def forbidden(_):
        return jsonify(error="Forbidden"), 403

    @app.errorhandler(404)
    def not_found(_):
        return jsonify(error="Resource not found"), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify(error="Method not allowed"), 405

    @app.errorhandler(413)
    def too_large(_):
        return jsonify(error="Request body too large"), 413

    @app.errorhandler(429)
    def rate_limited(_):
        return jsonify(error="Rate limit exceeded"), 429

    @app.errorhandler(Exception)
    def unhandled(_):
        app.logger.exception("Unhandled application error")
        return jsonify(error="Internal server error"), 500

    return app
