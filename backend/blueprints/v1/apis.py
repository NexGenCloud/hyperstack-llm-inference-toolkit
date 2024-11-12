import typing
import time
import uuid

from flask import Blueprint, request
from flask import jsonify, Response, current_app as app
from sqlalchemy import and_
from sqlalchemy.orm import Session

from config import Config
from utils.db import db, with_session
from utils.rest import validate_request, ensure_api_key, ensure_admin_api_key
from utils.rate_limits import ensure_api_key_rate_limits
from utils.request_handlers import (
    handle_streaming_request,
    handle_non_streaming_request,
)
from utils.mock import handle_mock_streaming_request, handle_mock_non_streaming_request
from tables.api_key import APIKey, APIKeySchema
from tables.llm_model import LLMModel, LLMModelSchema
from tables.replicas import Replica, ReplicaSchema, ReplicaVMStatus
from tables.metrics import Metric
from tables.replica_security_rule import ReplicaSecurityRule
from worker.tasks import create_vm_on_hyperstack

from .schemas import (
    ChatCompletionRequestSchema,
    GenerateAPIKeyRequestSchema,
    ReplicaRequestSchema,
    LLMModeLRequestSchema,
    ReplicaUpdateSchema,
    DeleteAPIKeyRequestSchema,
)

v1_bp = Blueprint("v1", __name__)


@v1_bp.route("/generate_api_key", methods=["POST"])
@validate_request(GenerateAPIKeyRequestSchema)
@ensure_admin_api_key()
@with_session
def generate_api_key(
    session: Session, validated_data: typing.Dict[str, typing.Any]
) -> Response:
    """
    Generate an API key for a user.
    """
    user_id = validated_data["user_id"]
    api_key = APIKey(user_id=user_id, api_key=str(uuid.uuid4()), enabled=True)
    session.add(api_key)
    session.commit()
    api_key_schema = APIKeySchema(only=("api_key", "id", "enabled"))
    return jsonify(api_key_schema.dump(api_key)), 200


@v1_bp.route("/delete_api_key", methods=["POST"])
@validate_request(DeleteAPIKeyRequestSchema)
@ensure_admin_api_key()
@with_session
def delete_api_key(
    session: Session, validated_data: typing.Dict[str, typing.Any]
) -> Response:
    """
    Delete an API key for a user.
    """
    user_id = validated_data["user_id"]
    api_key_id = validated_data["api_key_id"]
    api_key = (
        session.query(APIKey).filter_by(user_id=user_id, id=api_key_id).one_or_none()
    )
    if not api_key:
        return (
            jsonify(
                {"error": "API key not found for the given user_id and api_key_id"}
            ),
            404,
        )
    # check if already disabled
    if not api_key.enabled:
        return jsonify({"message": "API key already disabled"}), 409

    # Check if the API key has been used (assuming there's a metrics table to check)
    metrics_entry = session.query(Metric).filter_by(api_key_id=api_key_id).first()
    if metrics_entry:
        api_key.enabled = False
        session.commit()
        return jsonify({"message": "API key disabled successfully"}), 200

    session.delete(api_key)
    session.commit()
    return jsonify({"message": "API key deleted successfully"}), 200


@v1_bp.route("/chat/completions", methods=["POST"])
@ensure_api_key(include_api_key=True)
@ensure_api_key_rate_limits
@validate_request(ChatCompletionRequestSchema)
@with_session
def chat_completions(
    session: Session, validated_data: typing.Dict[str, typing.Any], key: APIKey
) -> Response:
    """
    Handle a chat completion request from the LLM endpoint API,
    stream the response back to the client and update the API
    key usage metrics.
    """
    raw = validated_data.pop("raw_stream_response")
    start_time = time.time()
    model = (
        session.query(LLMModel).filter_by(name=validated_data["model"]).one_or_none()
    )
    if not model:
        return jsonify({"error": "Invalid Model"}), 400

    replica = (
        session.query(Replica)
        .filter_by(model_id=model.id, vm_status=ReplicaVMStatus.SUCCESS)
        .first()
    )
    if not replica:
        return jsonify({"error": "No Replica available / ready."}), 400

    if not replica.endpoint:
        return jsonify({"error": "Missing endpoint url."}), 400

    llm_api_url = replica.endpoint

    if app.config["MOCK_LLM"]:
        # Mock LLM Calls during testing
        if validated_data["stream"]:
            response = handle_mock_streaming_request()
        else:
            response = handle_mock_non_streaming_request()
    else:
        if validated_data["stream"]:
            response = handle_streaming_request(
                session=session,
                api_key_id=key.id,
                endpoint=llm_api_url,
                start_time=start_time,
                chat_completion_payload=validated_data,
                raw=raw,
            )
        else:
            response = handle_non_streaming_request(
                session=session,
                api_key_id=key.id,
                endpoint=llm_api_url,
                start_time=start_time,
                chat_completion_payload=validated_data,
            )

    return response


@v1_bp.route("/tables", methods=["GET"])
@ensure_admin_api_key()
def list_tables() -> Response:
    return jsonify({"tables": list(db.metadata.tables.keys())})


@v1_bp.route("/tables/<string:table_name>", methods=["GET"])
@ensure_admin_api_key()
@with_session
def get_table_data(session: Session, table_name: str) -> Response:
    """
    Retrieve the first 100 rows of data for a given table.
    FIXME: Limit is top 100 for now, need to add pagination before
           elevating the limit.
    """
    if table_name in db.metadata.tables:
        table_class = db.metadata.tables[table_name]
        query = (
            session.query(table_class)
            .order_by(table_class.columns.id.desc())
            .limit(100)
            .all()
        )
        return jsonify(
            {"data": [dict(zip(table_class.columns.keys(), row)) for row in query]}
        )
    else:
        return jsonify({"error": "Detail not found"}), 404


@v1_bp.route("/models", methods=["GET"])
@ensure_admin_api_key()
@with_session
def get_all_models(session: Session) -> Response:
    """
    Get all models.
    """
    models = session.query(LLMModel)
    if request.args.get("active"):
        models = models.join(
            Replica,
            and_(
                Replica.model_id == LLMModel.id,
                Replica.vm_status == ReplicaVMStatus.SUCCESS,
            ),
        )
    models = models.all()
    model_schema = LLMModelSchema(many=True)
    return jsonify(model_schema.dump(models)), 200


@v1_bp.route("/models/<string:model_name>", methods=["GET"])
@ensure_admin_api_key()
@with_session
def get_model(session: Session, model_name: str) -> Response:
    """
    Get a single model details.
    """
    model = session.query(LLMModel).filter_by(name=model_name).one_or_none()
    model_schema = LLMModelSchema()
    return jsonify(model_schema.dump(model)), 200


@v1_bp.route("/models", methods=["POST"])
@validate_request(LLMModeLRequestSchema)
@ensure_admin_api_key()
@with_session
def create_model(
    session: Session, validated_data: typing.Dict[str, typing.Any]
) -> Response:
    """
    Create a model.
    """
    model_name = validated_data["name"]
    model = session.query(LLMModel).filter_by(name=model_name).one_or_none()
    if model:
        return jsonify({"message": "Model already exists."}), 400
    model = LLMModel(name=model_name)
    session.add(model)
    session.commit()
    return jsonify({"model_name": model_name, "id": model.id}), 201


@v1_bp.route("/models/<int:model_id>", methods=["DELETE"])
@ensure_admin_api_key()
@with_session
def delete_model(session: Session, model_id: int) -> Response:
    """
    Delete an model.
    """
    # First deleting all replicas for that given model
    replicas = session.query(Replica.id).filter_by(model_id=model_id).all()
    replica_ids = [replica.id for replica in replicas]
    (
        session.query(ReplicaSecurityRule)
        .filter(ReplicaSecurityRule.replica_id.in_(replica_ids))
        .delete()
    )
    (session.query(Replica).filter_by(model_id=model_id).delete())
    session.query(LLMModel).filter_by(id=model_id).delete()
    session.commit()
    return jsonify({}), 204


@v1_bp.route("/models/<int:model_id>/replicas", methods=["GET"])
@ensure_admin_api_key()
@with_session
def get_models_replicas(session: Session, model_id: int) -> Response:
    """
    Get all replica for given model.
    """
    replicas = session.query(Replica).filter_by(model_id=model_id).all()
    replica_schema = ReplicaSchema(many=True, exclude=("model",))
    return jsonify(replica_schema.dump(replicas)), 200


@v1_bp.route("/models/<int:model_id>/replicas", methods=["POST"])
@ensure_admin_api_key()
@validate_request(ReplicaRequestSchema)
@with_session
def create_models_replicas(
    session: Session, validated_data: typing.Dict[str, typing.Any], model_id: int
) -> Response:
    """
    Create a replica for given model.model_name
    """
    create_vm = validated_data.pop("create_vm")
    model = session.query(LLMModel).filter_by(id=model_id).one_or_none()
    if not model:
        return jsonify({"error": "Model not found"}), 404

    if not create_vm:
        replica = (
            session.query(Replica)
            .filter_by(model_id=model_id, endpoint=validated_data["endpoint"])
            .one_or_none()
        )
        if replica:
            return jsonify({"error": "Endpoint already exists"}), 400

    # preparing data
    validated_data = {
        **validated_data,
        **validated_data.get("vm_creation_details", {}),
        "vm_status": ReplicaVMStatus.PENDING if create_vm else ReplicaVMStatus.SUCCESS,
        "model_id": model.id,
    }

    replica = Replica.create(session, **validated_data)

    if create_vm:
        validated_data["security_rules"] = [
            {
                "direction": "ingress",
                "protocol": "tcp",
                "ethertype": "IPv4",
                "remote_ip_prefix": Config.PUBLIC_IP,
                "port_range_min": validated_data["port"],
                "port_range_max": validated_data["port"],
            },
            {
                "direction": "ingress",
                "protocol": "tcp",
                "ethertype": "IPv4",
                "remote_ip_prefix": "0.0.0.0/0",
                "port_range_min": 22,
                "port_range_max": 22,
            },
        ]
        security_group_rules = [
            {**rule, "replica_id": replica.id}
            for rule in validated_data["security_rules"]
        ]
        ReplicaSecurityRule.batch_create(session, security_group_rules)
        try:
            create_vm_on_hyperstack(replica.id, validated_data)
        except RuntimeError as e:
            return jsonify({"error": str(e)}), 400

    return jsonify({"replica_id": replica.id}), 201


@v1_bp.route("/models/replicas/<int:replica_id>", methods=["PUT"])
@ensure_admin_api_key()
@validate_request(ReplicaUpdateSchema)
@with_session
def update_replica(
    session: Session, validated_data: typing.Dict[str, typing.Any], replica_id: int
) -> Response:
    """
    Create a replica for given model.
    """
    replica = session.query(Replica).filter_by(id=replica_id).one_or_none()
    if not replica:
        return jsonify({"error": "Replica not found"}), 404
    replica = Replica.update(session, replica, **validated_data)
    return jsonify({}), 204


@v1_bp.route("/replicas/<int:replica_id>", methods=["DELETE"])
@ensure_admin_api_key()
@with_session
def delete_replica(session: Session, replica_id: int) -> Response:
    """
    Delete replica.
    """
    # First deleting all replicas for that given model
    session.query(ReplicaSecurityRule).filter_by(replica_id=replica_id).delete()
    session.query(Replica).filter_by(id=replica_id).delete()
    session.commit()
    return jsonify({}), 204
