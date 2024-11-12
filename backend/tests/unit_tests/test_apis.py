import os
import pytest
from unittest.mock import patch

from tables.metrics import Metric
from tables.api_key import APIKey
from tables.llm_model import LLMModel
from tables.replicas import Replica, ReplicaVMStatus

from .factories import APIKeyFactory, MetricFactory, LLMModelFactory, ReplicaFactory
from .utils import AIModel


class TestGenerateAPIKeyEndpoint:
    """
    Tests for the generate_api_key API endpoint.
    """

    @pytest.mark.parametrize(
        "payload, expected_error",
        [
            ({}, ["Missing data for required field."]),
        ],
    )
    def test_generate_api_key_errors(self, api_client, payload, expected_error):
        """
        Test validation errors.
        """
        response = api_client.post(
            "/api/v1/generate_api_key",
            json=payload,
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )

        assert response.status_code == 400
        assert response.json["errors"]["user_id"] == expected_error

    def test_generate_api_key_success(self, db_session, api_client):
        """
        Test successful API key generation.
        """
        user_id = "test"
        model_name = AIModel.MISTRALAI
        model = LLMModelFactory(name=model_name)
        ReplicaFactory.create_batch(2, llm_model=model)
        response = api_client.post(
            "/api/v1/generate_api_key",
            json={"user_id": user_id},
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        key = db_session.query(APIKey).filter_by(user_id=user_id).first()

        assert response.status_code == 200
        assert response.json == {
            "api_key": key.api_key,
            "enabled": key.enabled,
            "id": key.id,
        }


class TestDeleteAPIKeyEndpoint:
    """
    Tests for the delete_api_key API endpoint.
    """

    def test_delete_api_key_success(self, db_session, api_client):
        """
        Test successful API key deletion.
        """
        api_key = APIKeyFactory(enabled=True)
        response = api_client.post(
            "/api/v1/delete_api_key",
            json={"user_id": api_key.user_id, "api_key_id": api_key.id},
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )

        assert response.status_code == 200
        assert response.json == {"message": "API key deleted successfully"}
        key = db_session.query(APIKey).filter_by(id=api_key.id).one_or_none()
        assert key is None

    def test_delete_api_key_not_found(self, api_client):
        """
        Test API key not found error.
        """
        response = api_client.post(
            "/api/v1/delete_api_key",
            json={"user_id": "nonexistent_user", "api_key_id": 999},
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )

        assert response.status_code == 404
        assert response.json == {
            "error": "API key not found for the given user_id and api_key_id"
        }

    def test_delete_api_key_with_metrics(self, db_session, api_client):
        """
        Test deleting an API key that has associated metrics.
        """

        metric = MetricFactory()
        api_key = metric.api_key
        response = api_client.post(
            "/api/v1/delete_api_key",
            json={"user_id": api_key.user_id, "api_key_id": api_key.id},
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )

        assert response.status_code == 200
        assert response.json == {"message": "API key disabled successfully"}
        key = db_session.query(APIKey).filter_by(id=api_key.id).one_or_none()
        assert key is not None
        assert key.enabled is False


class TestChatCompletionsEndpoint:
    """
    Tests for the chat_completions API endpoint.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        # api key with MISTRALAI model
        APIKeyFactory()
        # api key with PERPLEXITY model
        self.auth = APIKeyFactory()

    @pytest.mark.parametrize(
        "payload, expected_error",
        [
            (
                {"model": AIModel.PERPLEXITY, "stream": False, "messages": []},
                {"errors": {"messages": ["Shorter than minimum length 1."]}},
            ),
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user"}],
                },
                {
                    "errors": {
                        "messages": {
                            "0": {"content": ["Missing data for required field."]}
                        }
                    }
                },
            ),
            (
                {
                    "model": "",
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                },
                {"errors": {"model": ["Model must not be empty."]}},
            ),
            (
                {
                    "model": "unsupported_model",
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                },
                {
                    "errors": {
                        "model": ["Model name 'unsupported_model' is not supported."]
                    }
                },
            ),
            (
                {
                    "model": AIModel.MISTRALAI,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                },
                {"error": "No Replica available / ready."},
            ),
            # Validation for invalid stop sequence
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "stop": 123,
                },
                {
                    "errors": {
                        "stop": ["stop must be either a string or a list of strings"]
                    }
                },
            ),
            # Validation for invalid stop sequence
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "stop": ["valid_stop", 123],
                },
                {"errors": {"stop": ["All elements in the stop list must be strings"]}},
            ),
            # Validation for presence_penalty out of range
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "presence_penalty": 3,
                },
                {
                    "errors": {
                        "presence_penalty": [
                            "Must be greater than or equal to -2.0 and less than or equal to 2.0."
                        ]
                    }
                },
            ),
            # Validation for frequency_penalty out of range
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "frequency_penalty": -3,
                },
                {
                    "errors": {
                        "frequency_penalty": [
                            "Must be greater than or equal to -2.0 and less than or equal to 2.0."
                        ]
                    }
                },
            ),
            # Validation for temperature out of range
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "temperature": 3,
                },
                {
                    "errors": {
                        "temperature": [
                            "Must be greater than or equal to 0.0 and less than or equal to 2.0."
                        ]
                    }
                },
            ),
            # Validation for top_p out of range
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "top_p": 1.5,
                },
                {
                    "errors": {
                        "top_p": [
                            "Must be greater than or equal to 0.0 and less than or equal to 1.0."
                        ]
                    }
                },
            ),
            # Validation for top_logprobs when logprobs is not set to True
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "top_logprobs": 15,
                },
                {
                    "errors": {
                        "top_logprobs": [
                            "top_logprobs can only be set if logprobs is True"
                        ]
                    }
                },
            ),
            # Validation for top_logprobs out of range
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "logprobs": True,
                    "top_logprobs": 25,
                },
                {
                    "errors": {
                        "top_logprobs": [
                            "Must be greater than or equal to 0 and less than or equal to 20."
                        ]
                    }
                },
            ),
            # Validation for max_tokens out of range
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "max_tokens": -1,
                },
                {"errors": {"max_tokens": ["Must be greater than or equal to 1."]}},
            ),
            # Validation for logit_bias values range
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "logit_bias": {"token_id": 150},
                },
                {
                    "errors": {
                        "logit_bias": {
                            "token_id": {
                                "value": [
                                    "Must be greater than or equal to -100 and less than or equal to 100."
                                ]
                            }
                        }
                    }
                },
            ),
            # Validation for invalid type for stream_options
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "stream_options": "invalid_option",
                },
                {"errors": {"stream_options": {"_schema": ["Invalid input type."]}}},
            ),
            # Validation for invalid string choice in tool_choice
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "tool_choice": "invalid_choice_value",
                },
                {
                    "errors": {
                        "tool_choice": [
                            ["Must be one of: none, auto, required."],
                            {"_schema": ["Invalid input type."]},
                        ]
                    }
                },
            ),
            # Validation for missing function name in tool_choice
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "tool_choice": {"type": "function"},
                },
                {
                    "errors": {
                        "tool_choice": [
                            ["Not a valid string."],
                            {"function": ["Missing data for required field."]},
                        ]
                    }
                },
            ),
            # Validation for invalid function type in tool_choice
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "tool_choice": {
                        "type": "invalid_type",
                        "function": {"name": "test_function"},
                    },
                },
                {
                    "errors": {
                        "tool_choice": [
                            ["Not a valid string."],
                            {"type": ["Must be equal to function."]},
                        ]
                    }
                },
            ),
            # Validation for invalid type in tools
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "tools": [
                        {"type": "invalid_type", "function": {"name": "test_function"}}
                    ],
                },
                {"errors": {"tools": {"0": {"type": ["Must be equal to function."]}}}},
            ),
            # Validation for missing function name in tools
            (
                {
                    "model": AIModel.PERPLEXITY,
                    "stream": False,
                    "messages": [{"role": "user", "content": "test message"}],
                    "tools": [
                        {"type": "function", "function": {"description": "testing"}}
                    ],
                },
                {
                    "errors": {
                        "tools": {
                            "0": {
                                "function": {
                                    "name": ["Missing data for required field."]
                                }
                            }
                        }
                    }
                },
            ),
        ],
    )
    def test_validation_errors(self, api_client, payload, expected_error):
        """
        Test cases for validation errors in the chat completion endpoint.
        """
        model1 = LLMModelFactory(name=AIModel.PERPLEXITY)
        model2 = LLMModelFactory(name=AIModel.MISTRALAI)
        ReplicaFactory.create_batch(
            2, llm_model=model1, vm_status=ReplicaVMStatus.SUCCESS
        )
        ReplicaFactory.create_batch(
            2, llm_model=model2, vm_status=ReplicaVMStatus.FAILED
        )
        response = api_client.post(
            "/api/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.auth.api_key}"},
        )
        assert response.status_code == 400
        assert response.json == expected_error

    def test_api_rate_limits(self, api_client):
        """
        Test case for API key rate limits.

        1) generate api key with 1 request per minute rate limit.
        2) make two requests with the same API key within a minute.
        """
        # One request per minute is allowed for the following api key
        allowed_rpm = 1
        model = LLMModelFactory(name=AIModel.PERPLEXITY)
        ReplicaFactory.create_batch(
            1, llm_model=model, vm_status=ReplicaVMStatus.SUCCESS
        )
        key = APIKeyFactory(allowed_rpm=allowed_rpm)
        payload = {
            "model": AIModel.PERPLEXITY,
            "stream": False,
            "messages": [{"role": "user", "content": "test message"}],
        }
        response = api_client.post(
            "/api/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {key.api_key}"},
        )
        assert response.status_code == 200

        # Second API request with the same API key will result in 429 status code
        response = api_client.post(
            "/api/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {key.api_key}"},
        )
        assert response.status_code == 429
        assert response.json == {
            "allowed_rpm": allowed_rpm,
            "error": "rate_limit_exceeded",
            "message": f"Rate limit exceeded: allowed {allowed_rpm} requests per minute.",
        }

    def test_non_streaming_response(self, api_client):
        """
        Test case for successful non-streamed chat completions.
        """
        model = LLMModelFactory(name=AIModel.PERPLEXITY)
        ReplicaFactory.create_batch(
            1, llm_model=model, vm_status=ReplicaVMStatus.SUCCESS
        )
        payload = {
            "model": AIModel.PERPLEXITY,
            "stream": False,
            "messages": [{"role": "user", "content": "test message"}],
        }
        response = api_client.post(
            "/api/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.auth.api_key}"},
        )
        assert response.status_code == 200
        assert response.json["id"] == "cmpl-0332ebd727cc4af19fa2d80035ab1e1f"
        assert response.json["object"] == "text_completion"
        assert response.json["created"] == 1716838725

    def test_streaming_response(self, api_client):
        """
        Test case for successful streamed chat completions.
        """
        model = LLMModelFactory(name=AIModel.PERPLEXITY)
        ReplicaFactory.create_batch(
            1, llm_model=model, vm_status=ReplicaVMStatus.SUCCESS
        )
        payload = {
            "model": AIModel.PERPLEXITY,
            "stream": True,
            "messages": [{"role": "user", "content": "test message"}],
        }
        response = api_client.post(
            "/api/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.auth.api_key}"},
        )
        assert response.status_code == 200
        assert response.mimetype == "text/event-stream"


class TestTableMetadataEndpoint:
    """
    Tests for the /api/v1/tables/* endpoints.
    """

    def test_get_tables(self, api_client):
        """
        Test tables retrieval.
        """
        response = api_client.get(
            "/api/v1/tables",
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )

        assert response.status_code == 200
        assert response.json["tables"] == [
            "api_key",
            "metric",
            "llm_models",
            "replicas",
            "replica_security_rules",
        ]

    @pytest.mark.parametrize(
        "factory_class, table_name, expected_keys",
        [
            (
                APIKeyFactory,
                "api_key",
                ["id", "user_id", "api_key", "allowed_rpm", "enabled"],
            ),
            (
                MetricFactory,
                "metric",
                [
                    "id",
                    "api_key_id",
                    "input",
                    "created",
                    "model",
                    "choices",
                    "prompt_tokens",
                    "total_tokens",
                    "completion_tokens",
                    "duration",
                ],
            ),
        ],
    )
    def test_get_table_data(self, api_client, factory_class, table_name, expected_keys):
        """
        Test table data retrieval.
        """
        expected_data = []
        for _ in range(5):
            instance = factory_class()
            data = {key: getattr(instance, key) for key in expected_keys}
            expected_data.append(data)

        response = api_client.get(
            f"/api/v1/tables/{table_name}",
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        assert response.status_code == 200
        assert len(response.json["data"]) == len(expected_data)
        assert response.json["data"] == sorted(expected_data, key=lambda x: -x["id"])


class TestLLMModelAPIs:

    def test_get_all_models(self, api_client, db_session):
        """
        Test retrieving all models.
        """
        LLMModelFactory.create_batch(2)

        response = api_client.get(
            "/api/v1/models",
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2

    def test_get_model(self, api_client, db_session):
        """
        Test retrieving a single model by name.
        """
        model = LLMModelFactory(name="Model1")

        response = api_client.get(
            f"/api/v1/models/{model.name}",
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Model1"

    def test_create_model(self, api_client, db_session):
        """
        Test creating a new model.
        """
        payload = {"name": "NewModel"}
        response = api_client.post(
            "/api/v1/models",
            json=payload,
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["model_name"] == "NewModel"

        model = db_session.query(LLMModel).filter_by(name="NewModel").one_or_none()
        assert model is not None

    def test_create_model_validation_error(self, api_client, db_session):
        """
        Test creating a new model with validation error.
        """
        payload = {}  # Missing 'name'
        response = api_client.post(
            "/api/v1/models",
            json=payload,
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "name" in data["errors"]

    def test_delete_model(self, api_client, db_session):
        """
        Test deleting a model by ID.
        """
        model = LLMModelFactory()

        response = api_client.delete(
            f"/api/v1/models/{model.id}",
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        assert response.status_code == 204

        model = db_session.query(LLMModel).filter_by(id=model.id).one_or_none()
        assert model is None

    def test_get_models_replicas(self, api_client, db_session):
        """
        Test retrieving all replicas for a given model.
        """
        model = LLMModelFactory()
        ReplicaFactory.create_batch(2, llm_model=model)

        response = api_client.get(
            f"/api/v1/models/{model.id}/replicas",
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2

    def test_create_models_replicas(self, api_client, db_session):
        """
        Test creating a new replica for a given model.
        """
        model = LLMModelFactory()

        payload = {
            "endpoint": "http://example.com/3",
            "rate_limit": 30,
        }
        response = api_client.post(
            f"/api/v1/models/{model.id}/replicas",
            json=payload,
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "replica_id" in data

    def test_create_models_replicas_validation_error(self, api_client, db_session):
        """
        Test creating a new replica with validation error.
        """
        model = LLMModelFactory()

        payload = {}
        response = api_client.post(
            f"/api/v1/models/{model.id}/replicas",
            json=payload,
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "endpoint" in data["errors"]

    def test_update_replica(self, api_client, db_session):
        """
        Test updating a replica by ID.
        """
        model = LLMModelFactory()
        replica = ReplicaFactory(llm_model=model)

        payload = {
            "rate_limit": 50,
        }
        response = api_client.put(
            f"/api/v1/models/replicas/{replica.id}",
            json=payload,
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        assert response.status_code == 204

        updated_replica = (
            db_session.query(Replica).filter_by(id=replica.id).one_or_none()
        )
        assert updated_replica.rate_limit == 50

    def test_update_replica_validation_error(self, api_client, db_session):
        """
        Test updating a replica with validation error.
        """
        model = LLMModelFactory()
        replica = ReplicaFactory(llm_model=model)

        payload = {
            # Missing 'rate_limit'
        }
        response = api_client.put(
            f"/api/v1/models/replicas/{replica.id}",
            json=payload,
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "rate_limit" in data["errors"]

    def test_delete_replica(self, api_client, db_session):
        """
        Test deleting a replica by ID.
        """
        model = LLMModelFactory()
        replica = ReplicaFactory(llm_model=model)

        response = api_client.delete(
            f"/api/v1/replicas/{replica.id}",
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        assert response.status_code == 204

        deleted_replica = (
            db_session.query(Replica).filter_by(id=replica.id).one_or_none()
        )
        assert deleted_replica is None

    @patch("blueprints.v1.apis.create_vm_on_hyperstack")
    def test_create_models_replicas_with_vm_creation(self, _, api_client, db_session):
        """
        Test creating a new replica for a given model with vm creation.
        """
        model = LLMModelFactory()

        payload = {
            "endpoint": "",
            "rate_limit": 30,
            "create_vm": True,
            "vm_creation_details": {
                "name": "inference-vm-2",
                "environment_name": "default-CANADA-1",
                "image_name": "Ubuntu Server 22.04 LTS R535 CUDA 12.2",
                "flavor_name": "n1-RTX-A6000x1",
                "assign_floating_ip": True,
                "key_name": "sample-key",
                "port": 8000,
                "security_rules": [
                    {
                        "direction": "ingress",
                        "protocol": "tcp",
                        "ethertype": "IPv4",
                        "remote_ip_prefix": "0.0.0.0/0",
                        "port_range_min": 8000,
                        "port_range_max": 8000,
                    },
                    {
                        "direction": "ingress",
                        "protocol": "tcp",
                        "ethertype": "IPv4",
                        "remote_ip_prefix": "0.0.0.0/0",
                        "port_range_min": 22,
                        "port_range_max": 22,
                    },
                ],
                "run_command": "SOME DUMMY COMMAND",
            },
        }
        response = api_client.post(
            f"/api/v1/models/{model.id}/replicas",
            json=payload,
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "replica_id" in data
        replica = (
            db_session.query(Replica).filter_by(id=data["replica_id"]).one_or_none()
        )
        assert replica.vm_status == ReplicaVMStatus.PENDING

    @pytest.mark.parametrize(
        "payload, expected_error, missing_key",
        [
            # Missing image name for VM creation
            (
                {
                    "rate_limit": 30,
                    "create_vm": True,
                    "vm_creation_details": {
                        "name": "inference-vm-2",
                        "environment_name": "default-CANADA-1",
                        "flavor_name": "n1-RTX-A6000x1",
                        "assign_floating_ip": True,
                        "security_rules": [
                            {
                                "direction": "ingress",
                                "protocol": "tcp",
                                "ethertype": "IPv4",
                                "remote_ip_prefix": "0.0.0.0/0",
                                "port_range_min": 8000,
                                "port_range_max": 8000,
                            }
                        ],
                        "run_command": "SOME DUMMY COMMAND",
                        "key_name": "example-key",
                    },
                },
                "Missing data for required field.",
                "image_name",
            ),
            # Missing environment name for VM creation
            (
                {
                    "rate_limit": 30,
                    "create_vm": True,
                    "vm_creation_details": {
                        "name": "inference-vm-2",
                        "image_name": "Ubuntu Server 22.04 LTS R535 CUDA 12.2",
                        "flavor_name": "n1-RTX-A6000x1",
                        "assign_floating_ip": True,
                        "security_rules": [
                            {
                                "direction": "ingress",
                                "protocol": "tcp",
                                "ethertype": "IPv4",
                                "remote_ip_prefix": "0.0.0.0/0",
                                "port_range_min": 8000,
                                "port_range_max": 8000,
                            }
                        ],
                        "run_command": "SOME DUMMY COMMAND",
                        "key_name": "example-key",
                    },
                },
                "Missing data for required field.",
                "environment_name",
            ),
        ],
    )
    def test_create_models_replicas_with_validation_errors(
        self, api_client, payload, expected_error, missing_key
    ):
        """
        Test creating a new replica with various validation errors.
        """
        model = LLMModelFactory()

        response = api_client.post(
            f"/api/v1/models/{model.id}/replicas",
            json=payload,
            headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert expected_error in data["errors"]["vm_creation_details"][missing_key]
