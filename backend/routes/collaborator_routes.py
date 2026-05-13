from flask import Blueprint, request

from routes.helpers import json_data, json_error, require_admin
from services import collaborator_service

collaborator_bp = Blueprint("collaborators", __name__)


@collaborator_bp.route("/v1/collaborators", methods=["GET"])
def list_collaborators():
    auth_error = require_admin()
    if auth_error:
        return auth_error

    limit = request.args.get("limit", default=20, type=int)
    offset = request.args.get("offset", default=0, type=int)

    collaborators, meta = collaborator_service.list_collaborators(limit, offset)

    return json_data(collaborators, meta=meta)


@collaborator_bp.route("/v1/collaborators/<int:collaborator_id>", methods=["GET"])
def get_collaborator(collaborator_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error

    collaborator = collaborator_service.get_collaborator(collaborator_id)

    if collaborator is None:
        return json_error("NOT_FOUND", "Colaborador nao encontrado.", status=404)

    return json_data(collaborator)


@collaborator_bp.route("/v1/collaborators", methods=["POST"])
def create_collaborator():
    auth_error = require_admin()
    if auth_error:
        return auth_error

    try:
        payload = request.get_json(silent=True) or {}
        collaborator = collaborator_service.create_collaborator(payload)

        return json_data(collaborator, status=201)

    except ValueError as exc:
        return json_error("INVALID_INPUT", str(exc), status=400)

    except Exception as exc:
        if collaborator_service.is_integrity_error(exc):
            return json_error(
                "CONFLICT",
                "Ja existe colaborador com esta matricula ou tag RFID.",
                status=409
            )

        raise


@collaborator_bp.route("/v1/collaborators/<int:collaborator_id>", methods=["PUT"])
def update_collaborator(collaborator_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error

    try:
        payload = request.get_json(silent=True) or {}
        collaborator = collaborator_service.update_collaborator(collaborator_id, payload)

        if collaborator is None:
            return json_error("NOT_FOUND", "Colaborador nao encontrado.", status=404)

        return json_data(collaborator)

    except ValueError as exc:
        return json_error("INVALID_INPUT", str(exc), status=400)

    except Exception as exc:
        if collaborator_service.is_integrity_error(exc):
            return json_error(
                "CONFLICT",
                "Ja existe colaborador com esta matricula ou tag RFID.",
                status=409
            )

        raise


@collaborator_bp.route("/v1/collaborators/<int:collaborator_id>", methods=["DELETE"])
def delete_collaborator(collaborator_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error

    deleted = collaborator_service.delete_collaborator(collaborator_id)

    if not deleted:
        return json_error("NOT_FOUND", "Colaborador nao encontrado.", status=404)

    return "", 204
