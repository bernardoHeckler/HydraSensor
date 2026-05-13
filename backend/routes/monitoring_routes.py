from flask import Blueprint

from routes.helpers import json_data
from services.monitoring_service import get_monitoring_summary

monitoring_bp = Blueprint("monitoring", __name__)


@monitoring_bp.route("/v1/monitoring/summary", methods=["GET"])
def monitoring_summary():
    return json_data(get_monitoring_summary())
