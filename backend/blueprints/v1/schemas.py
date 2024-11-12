from flask import request
from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from marshmallow_union import Union

from utils.db import db
from utils.rest import get_api_key
from tables.api_key import APIKey
from tables.llm_model import LLMModel
from tables.replicas import Replica


class GenerateAPIKeyRequestSchema(Schema):
    """
    Generate API key request schema which is what is expected by the generate API key endpoint.
    """

    user_id = fields.Str(required=True, validate=validate.Length(min=1))
    allowed_rpm = fields.Int()


class DeleteAPIKeyRequestSchema(Schema):
    """
    Delete API key request schema which is what is expected by the delete API key endpoint.
    """

    user_id = fields.Str(required=True)
    api_key_id = fields.Int(required=True)


class ContentItemSchema(Schema):
    type = fields.Str(
        required=True,
        validate=validate.OneOf(["text", "image", "video"]),
        metadata={"description": "Type of content item."},
    )
    text = fields.Str(metadata={"description": 'Text content (if type is "text").'})


class ChatCompletionMessageSchema(Schema):
    role = fields.Str(
        required=True,
        validate=validate.OneOf(["system", "user", "assistant"]),
        metadata={
            "description": "The role of the message sender (system, user, or assistant)."
        },
    )
    content = fields.Raw(
        required=True,
        metadata={
            "description": "Message content, which can be a simple string or a structured content item."
        },
    )
    extra_field = fields.Str(
        metadata={"description": "An extra field for extra_fields test"}
    )


class ChatCompletionStreamOptionsSchema(Schema):
    include_usage = fields.Bool(
        load_default=True,
        metadata={
            "description": (
                "If set, an additional chunk will be streamed before the `data: [DONE]` message. "
                "The `usage` field on this chunk shows the token usage statistics for the entire "
                "request, and the `choices` field will always be an empty array. All other chunks "
                "will also include a `usage` field, but with a null value."
            )
        },
    )


class FunctionSchema(Schema):
    name = fields.Str(
        required=True, metadata={"description": "The name of the function to call."}
    )
    description = fields.Str(metadata={"description": "A description of the function."})
    parameters = fields.Dict(
        metadata={
            "description": "The parameters the function accepts, described as a JSON Schema object."
        }
    )


class ChatCompletionNamedToolSchema(Schema):
    function = fields.Nested(
        FunctionSchema, required=True, metadata={"description": "The function to call."}
    )
    type = fields.Str(
        required=True,
        validate=validate.Equal("function"),
        metadata={
            "description": "The type of the tool. Currently, only `function` is supported."
        },
    )


class ResponseFormatSchema(Schema):
    type = fields.Str(
        required=True,
        validate=validate.OneOf(["text", "json_object"]),
        metadata={"description": "The format that the model must output."},
    )


class ChatCompletionRequestSchema(Schema):
    """
    Chat completion request schema which is what is expected by the chat completions endpoint.

    openai-v1.34.0 docs:
    https://platform.openai.com/docs/api-reference/chat/create

    Complies with the OpenAI API specification for chat completions:
    https://github.com/openai/openai-python/blob/v1.34.0/src/openai/types/chat/completion_create_params.py
    """

    # Required parameters
    messages = fields.List(
        fields.Nested(ChatCompletionMessageSchema),
        required=True,
        validate=validate.Length(min=1),
        metadata={
            "description": "A list of messages comprising the conversation so far."
        },
    )
    model = fields.Str(
        required=True, metadata={"description": "ID of the model to use."}
    )

    # Specifying defaults from https://platform.openai.com/docs/api-reference/chat/create
    # Group 1: Generation parameters
    max_tokens = fields.Int(
        validate=validate.Range(min=1),
        metadata={
            "description": "The maximum number of tokens that can be generated in the chat completion."
        },
    )
    n = fields.Int(
        load_default=1,
        validate=validate.Range(min=1),
        metadata={
            "description": "How many chat completion choices to generate for each input message."
        },
    )
    stop = fields.Raw(
        # No default value specified upstream
        metadata={
            "description": "Up to 4 sequences where the API will stop generating further tokens."
        }
    )

    # Group 2: Sampling parameters
    frequency_penalty = fields.Float(
        load_default=0,
        validate=validate.Range(min=-2.0, max=2.0),
        metadata={
            "description": (
                "Positive values penalize new tokens based on their existing frequency in the text so far, "
                "decreasing the model's likelihood to repeat the same line verbatim."
            )
        },
    )
    presence_penalty = fields.Float(
        load_default=0,
        validate=validate.Range(min=-2.0, max=2.0),
        metadata={
            "description": (
                "Positive values penalize new tokens based on whether they appear in the text so far, increasing "
                "the model's likelihood to talk about new topics."
            )
        },
    )
    temperature = fields.Float(
        load_default=1,
        validate=validate.Range(min=0.0, max=2.0),
        metadata={
            "description": (
                "Sampling temperature to use, between 0 and 2. Higher values make the output more random, while "
                "lower values make it more focused and deterministic."
            )
        },
    )

    # Group 3: Streaming parameters
    stream = fields.Bool(
        load_default=False,
        metadata={
            "description": (
                "If set to true, partial message deltas will be sent, like in ChatGPT. Tokens will be sent as "
                "data-only server-sent events as they become available, with the stream terminated by "
                "a `data: [DONE]` message."
            )
        },
    )
    stream_options = fields.Nested(
        ChatCompletionStreamOptionsSchema,
        metadata={"description": "Options for streaming response."},
    )

    # Group 4: Low-level sampling parameters
    logit_bias = fields.Dict(
        keys=fields.Str(),
        values=fields.Int(validate=validate.Range(min=-100, max=100)),
        metadata={
            "description": "Modify the likelihood of specified tokens appearing in the completion."
        },
    )
    logprobs = fields.Bool(
        load_default=False,
        metadata={
            "description": "Whether to return log probabilities of the output tokens or not."
        },
    )
    top_logprobs = fields.Int(
        metadata={
            "description": (
                "An integer between 0 and 20 specifying the number of most likely tokens "
                "to return at each token position, each with an associated log probability."
            )
        }
    )
    top_p = fields.Float(
        load_default=1,
        validate=validate.Range(min=0.0, max=1.0),
        metadata={
            "description": (
                "An alternative to sampling with temperature, called nucleus sampling, where the model considers "
                "the results of the tokens with top_p probability mass."
            )
        },
    )
    seed = fields.Int(
        metadata={
            "description": (
                "If specified, the system will make a best effort to sample deterministically, such that "
                "repeated requests with the same seed and parameters should return the same result."
            )
        }
    )
    response_format = fields.Nested(
        ResponseFormatSchema,
        metadata={
            "description": "An object specifying the format that the model must output."
        },
    )

    # Group 5: Tool/functions parameters
    # We don't add parallel_tool_calls because it's not supported upstream by vllm
    # https://github.com/vllm-project/vllm/blob/329df38f1a931215062d7b43660ceee1f83c0ab5/vllm/entrypoints/
    # openai/protocol.py#L129
    tool_choice = Union(
        [
            fields.Str(validate=validate.OneOf(["none", "auto", "required"])),
            fields.Nested(ChatCompletionNamedToolSchema),
        ],
        metadata={
            "description": (
                "Controls which (if any) tool is called by the model. none means the model will not call any tool and "
                "instead generates a message. auto means the model can pick between generating a message or calling "
                "one or more tools. required means the model must call one or more tools. Specifying a particular "
                'tool via `{ "type": "function", "function": {"name": "my_function"} }` forces the model to call '
                "that tool."
            )
        },
    )
    tools = fields.List(
        fields.Nested(ChatCompletionNamedToolSchema),
        metadata={
            "description": (
                "A list of tools the model may call. Currently, only functions are supported as a tool. Use this to "
                "provide a list of functions the model may generate JSON inputs for. A max of 128 functions "
                "are supported."
            )
        },
    )

    # Group 6: Identity parameters
    user = fields.Str(
        metadata={
            "description": (
                "A unique identifier representing your end-user, which can help OpenAI to monitor and detect abuse."
            )
        }
    )

    # Group 7: Deprecated parameters
    # functions and function_call are deprecated in favor of tools and tool_choice
    function_call = Union(
        [
            fields.Str(validate=validate.OneOf(["none", "auto"])),
            fields.Nested(ChatCompletionNamedToolSchema),
        ],
        metadata={
            "description": (
                "Deprecated in favor of tool_choice.\n\n"
                "Controls which (if any) function is called by the model. none means the model "
                "will not call a function and instead generates a message. auto means the model can "
                "pick between generating a message or calling a function. Specifying a particular function "
                'via {"name": "my_function"} forces the model to call that function.'
            )
        },
    )
    functions = fields.List(
        fields.Nested(FunctionSchema),
        metadata={
            "description": (
                "Deprecated in favor of tools.\n\n"
                "A list of functions the model may generate JSON inputs for."
            )
        },
    )
    guided_json = fields.Dict(
        metadata={"description": "JSON schema to guide the completion."}
    )
    guided_decoding_backend = fields.Str(
        metadata={"description": "Backend to use for guided decoding."}
    )
    guided_choice = fields.List(
        fields.Str(),
        metadata={"description": "List of strings to guide the completion choice."},
    )
    guided_regex = fields.Str(metadata={"description": "Regex for guided regex test"})
    raw_stream_response = fields.Bool(
        load_default=True,
        metadata={"description": "Flag to return raw stream response"},
    )

    @validates_schema
    def validate_model(self, data, **kwargs):
        model_name = data.get("model")
        if not model_name:
            raise ValidationError("Model must not be empty.", field_name="model")

        models = (
            db.session.query(LLMModel)
            .join(Replica, Replica.model_id == LLMModel.id)
            .all()
        )
        models = [model.name for model in models]
        if model_name not in models:
            raise ValidationError(
                f"Model name {model_name!r} is not supported.", field_name="model"
            )

        is_valid = (
            db.session.query(APIKey).filter_by(api_key=get_api_key(request)).first()
        )
        if not is_valid:
            raise ValidationError("Invalid API key.", field_name="model")

    @validates_schema
    def validate_top_logprobs(self, data, **kwargs):
        """
        Validate that top_logprobs is only set if logprobs is set.
        """
        top_logprobs = data.get("top_logprobs")
        logprobs = data.get("logprobs")
        if top_logprobs is not None:
            if not logprobs:
                raise ValidationError(
                    "top_logprobs can only be set if logprobs is True",
                    field_name="top_logprobs",
                )

            if top_logprobs < 0 or top_logprobs > 20:
                raise ValidationError(
                    "Must be greater than or equal to 0 and less than or equal to 20.",
                    field_name="top_logprobs",
                )

    @validates_schema
    def validate_stop(self, data, **kwargs):
        """
        Validate that stop is either a string or a list of strings.
        """
        stop = data.get("stop")
        if stop is not None and not isinstance(stop, (str, list)):
            raise ValidationError(
                "stop must be either a string or a list of strings", field_name="stop"
            )
        if isinstance(stop, list) and any(not isinstance(item, str) for item in stop):
            raise ValidationError(
                "All elements in the stop list must be strings", field_name="stop"
            )

    @validates_schema
    def validate_stream_options(self, data, **kwargs):
        """
        adds stream_options if stream is True
        """
        if data.get("stream"):
            data["stream_options"] = {"include_usage": True}
        else:
            data.pop("stream_options", None)


class SecurityRuleSchema(Schema):
    """
    Schema for defining a security rule.

    Attributes:
        direction (str): The direction of traffic ('ingress' or 'egress'). Required.
        protocol (str): The network protocol (e.g., 'tcp', 'udp'). Required.
        ethertype (str): The Ethernet type ('IPv4' or 'IPv6'). Required.
        remote_ip_prefix (str): The IP address range. Required.
        port_range_min (int): The minimum port number. Required.
        port_range_max (int): The maximum port number. Required.
    """

    direction = fields.Str(
        validate=validate.OneOf(["ingress", "egress"]), missing="ingress"
    )
    protocol = fields.Str(validate=validate.OneOf(["tcp", "udp"]), missing="tcp")
    ethertype = fields.Str(validate=validate.OneOf(["IPv4", "IPv6"]), missing="IPv4")
    remote_ip_prefix = fields.Str(missing="0.0.0.0/0")
    port_range_min = fields.Int()
    port_range_max = fields.Int()

    @validates_schema
    def validate_port_ranges(self, data, **kwargs):
        port_range_min = data.get("port_range_min")
        port_range_max = data.get("port_range_max")

        if port_range_min is not None and not (0 <= port_range_min <= 65535):
            raise ValidationError(
                "Invalid port range. Must be between 0 and 65535.",
                field_name="port_range_min",
            )

        if port_range_max is not None and not (0 <= port_range_max <= 65535):
            raise ValidationError(
                "Invalid port range. Must be between 0 and 65535.",
                field_name="port_range_max",
            )

        if port_range_min > port_range_max:
            raise ValidationError(
                "port_range_min must be less than or equal to port_range_max.",
                field_name="port_range_min",
            )


class VMCreationSchema(Schema):
    name = fields.Str(
        required=True,
        validate=validate.Regexp(
            r"^[^ ][\w -]*[^ ]$",
            error="Invalid name format. Name must not start or end with a space "
            "and can contain alphanumeric characters, spaces, and hyphens.",
        ),
    )
    environment_name = fields.Str(required=True)
    image_name = fields.Str(required=True)
    flavor_name = fields.Str(required=True)
    assign_floating_ip = fields.Bool(missing=True)
    security_rules = fields.List(fields.Nested(SecurityRuleSchema))
    port = fields.Int(required=True)
    run_command = fields.Str(required=True)
    key_name = fields.Str(required=True)


class ReplicaRequestSchema(Schema):
    endpoint = fields.Str(allow_none=True)
    rate_limit = fields.Integer()
    create_vm = fields.Bool(missing=False)
    vm_creation_details = fields.Nested(VMCreationSchema)

    @validates_schema
    def validate_data(self, data, **kwargs):
        endpoint = data.get("endpoint")
        create_vm = data.get("create_vm")

        if not create_vm and not endpoint:
            raise ValidationError(
                "LLM EndPoint URL must not be empty.", field_name="endpoint"
            )

        if create_vm and "vm_creation_details" not in data:
            raise ValidationError(
                "VM creation details must be provided when create_vm is True."
            )


class ReplicaUpdateSchema(Schema):
    """
    Replica update schema
    """

    rate_limit = fields.Integer(required=True)


class LLMModeLRequestSchema(Schema):
    """
    Schema for LLM model CRUD endpoints
    """

    name = fields.Str(required=True)
