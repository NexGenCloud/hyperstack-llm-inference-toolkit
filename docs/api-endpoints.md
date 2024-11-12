# API endpoints - Hyperstack LLM Inference Toolkit

The Proxy API VM provides several RESTful API endpoints for managing models, replicas, and API keys and for interacting with LLMs.

---

## 2.1 `/generate_api_key` - Generate an API Key

- **Method**: `POST`
- **Description**: Creates a unique API key for a user, allowing access to the inference API.
- **Request Headers**:
  - **Authorization**: `Bearer <ADMIN_API_KEY>`
- **Request Schema**: `GenerateAPIKeyRequestSchema`
- **Response**:
  - **Success (200)**: JSON response containing the generated API key.
  - **Error**: Standard error message if key generation fails.

---

## 2.2 `/delete_api_key` - Delete an API Key

- **Method**: `POST`
- **Description**: Deletes a specified API key for a user (or disables it if the API key has been used).
- **Request Headers**:
  - **Authorization**: `Bearer <ADMIN_API_KEY>`
- **Request Schema**: `DeleteAPIKeyRequestSchema`
- **Response**:
  - **Success (200)**: JSON response confirming the deletion/disablement of the API key.
  - **Error (404)**: Returns an error if the API key is not found.
  - **Error (409)**: Returns an error if the API key is already disabled.

---

## 2.3 `/chat/completions` - Chat Completion

- **Method**: `POST`
- **Description**: Handles LLM chat completion requests by forwarding the input to the specified model's endpoint. The response can be streamed or non-streamed.
- **Request Schema**: `ChatCompletionRequestSchema`
- **Response**:
  - **Success**: LLM-generated response (either streamed or non-streamed).
  - **Error**: Returns error messages if the model or replica is unavailable, or the endpoint is missing.

---

## 2.4 `/tables` - List Database Tables

- **Method**: `GET`
- **Description**: Lists all available database tables in the toolkit.
- **Request Headers**:
  - **Authorization**: `Bearer <ADMIN_API_KEY>`
- **Response**: JSON object with a list of table names.

---

## 2.5 `/tables/<string:table_name>` - Get Table Data

- **Method**: `GET`
- **Description**: Retrieves the top 100 rows of data from a specified table. (Pagination to be implemented in future updates).
- **Request Headers**:
  - **Authorization**: `Bearer <ADMIN_API_KEY>`
- **Response**:
  - **Success**: JSON object with table data (up to 100 rows).
  - **Error (404)**: Returns an error if the specified table is not found.

---

## 2.6 `/models` - List All Models

- **Method**: `GET`
- **Description**: Retrieves all registered models, with an optional filter for active models (those with successful replicas).
- **Request Headers**:
  - **Authorization**: `Bearer <ADMIN_API_KEY>`
- **Response**: JSON object with model details.

---

## 2.7 `/models/<string:model_name>` - Get Model Details

- **Method**: `GET`
- **Description**: Retrieves detailed information about a specified model.
- **Request Headers**:
  - **Authorization**: `Bearer <ADMIN_API_KEY>`
- **Response**:
  - **Success**: JSON object with model data.
  - **Error**: Returns an error if the model is not found.

---

## 2.8 `/models` - Create Model

- **Method**: `POST`
- **Description**: Creates a new LLM model with the specified name.
- **Request Headers**:
  - **Authorization**: `Bearer <ADMIN_API_KEY>`
- **Request Schema**: `LLMModeLRequestSchema`
- **Response**:
  - **Success (201)**: JSON response with the new model's ID and name.
  - **Error**: Returns an error if a model with the specified name already exists.

---

## 2.9 `/models/<int:model_id>` - Delete Model

- **Method**: `DELETE`
- **Description**: Deletes a specified model, along with all its replicas and related security rules.
- **Request Headers**:
  - **Authorization**: `Bearer <ADMIN_API_KEY>`
- **Response**:
  - **Success (204)**: Returns an empty response on successful deletion.

---

## 2.10 `/models/<int:model_id>/replicas` - Get Model Replicas

- **Method**: `GET`
- **Description**: Retrieves all replicas associated with a specified model.
- **Request Headers**:
  - **Authorization**: `Bearer <ADMIN_API_KEY>`
- **Response**: JSON object with details of each replica.

---

## 2.11 `/models/<int:model_id>/replicas` - Create Model Replica

- **Method**: `POST`
- **Description**: Creates a replica for a specified model. If `create_vm` is true, triggers VM creation.
- **Request Headers**:
  - **Authorization**: `Bearer <ADMIN_API_KEY>`
- **Request Schema**: `ReplicaRequestSchema`
- **Response**:
  - **Success (201)**: JSON response with the new replica's ID.
  - **Error**: Returns an error if the model is not found or if a replica with the specified endpoint already exists.

---

## 2.12 `/models/replicas/<int:replica_id>` - Update Replica

- **Method**: `PUT`
- **Description**: Updates the configuration of a specified replica.
- **Request Headers**:
  - **Authorization**: `Bearer <ADMIN_API_KEY>`
- **Request Schema**: `ReplicaUpdateSchema`
- **Response**:
  - **Success (204)**: Returns an empty response on successful update.
  - **Error**: Returns an error if the replica is not found.

---

## 2.13 `/replicas/<int:replica_id>` - Delete Replica

- **Method**: `DELETE`
- **Description**: Deletes a specified replica and its related security rules.
- **Request Headers**:
  - **Authorization**: `Bearer <ADMIN_API_KEY>`
- **Response**:
  - **Success (204)**: Returns an empty response on successful deletion.

---

## Notes:

- **Admin API Key**: The admin API key is required for all endpoints except `/chat/completions`.
- **API Key**: An API key is required for the `/chat/completions` endpoint. This API key is linked to a specific user and model.
- **Rate Limiting**: The API enforces rate limits on requests for the `/chat/completions` endpoint per API key.
- **Mock Mode**: If `MOCK_LLM` is enabled, the VM uses mock responses for testing without actual model deployment.
