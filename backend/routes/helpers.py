from flask import jsonify, request

from config import ADMIN_TOKEN


def json_data(data, status=200, meta=None):
    response = {"data": data}

    if meta is not None:
        response["meta"] = meta

    return jsonify(response), status


def json_error(code, message, status=400, details=None):
    return jsonify({
        "error": {
            "code": code,
            "message": message,
            "details": details or []
        }
    }), status


def get_bearer_token():
    authorization = request.headers.get("Authorization", "")

    if not authorization.startswith("Bearer "):
        return None

    return authorization.replace("Bearer ", "", 1).strip()


def require_admin():
    token = get_bearer_token()

    if token != ADMIN_TOKEN:
        return json_error(
            "UNAUTHORIZED",
            "Token de administracao ausente ou invalido.",
            status=401
        )

    return None
