from flask import Blueprint

from routes.helpers import json_data
from services.device_service import fetch_device_bootstrap_data

device_bp = Blueprint("device", __name__)


@device_bp.route("/v1/device/bootstrap", methods=["GET"])
def device_bootstrap():
    return json_data(fetch_device_bootstrap_data())
