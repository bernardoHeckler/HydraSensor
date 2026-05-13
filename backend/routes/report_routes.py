from flask import Blueprint, request

from routes.helpers import json_data, json_error
from services.report_service import calculate_daily_presence

report_bp = Blueprint("reports", __name__)


@report_bp.route("/v1/reports/daily-presence", methods=["GET"])
def daily_presence():
    try:
        date_ref = request.args.get("date")
        collaborator_id = request.args.get("collaborator_id", type=int)

        report = calculate_daily_presence(
            date_ref=date_ref,
            collaborator_id=collaborator_id,
        )

        return json_data(report)

    except ValueError as exc:
        return json_error("INVALID_INPUT", str(exc), status=400)
