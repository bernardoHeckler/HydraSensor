import os

from flask import Flask, jsonify, send_from_directory

from config import BASE_DIR
from database import init_db
from routes.access_event_routes import access_event_bp
from routes.auth_routes import auth_bp
from routes.collaborator_routes import collaborator_bp
from routes.device_routes import device_bp
from routes.monitoring_routes import monitoring_bp
from routes.report_routes import report_bp

app = Flask(__name__)

init_db()

app.register_blueprint(auth_bp)
app.register_blueprint(collaborator_bp)
app.register_blueprint(access_event_bp)
app.register_blueprint(device_bp)
app.register_blueprint(monitoring_bp)
app.register_blueprint(report_bp)


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "5000")),
        debug=os.getenv("APP_DEBUG", "true").lower() == "true",
        use_reloader=os.getenv("APP_USE_RELOADER", "true").lower() == "true",
    )
