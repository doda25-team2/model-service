"""
Flask API of the SMS Spam detection model.
"""
# stdlib
import os
import json
from pathlib import Path

# external
import joblib
from flask import Flask, jsonify, request
from flasgger import Swagger
import requests

# internal
from config import OUTPUT_PATH
from text_preprocessing import prepare, _extract_message_len, _text_process

# Service version - should match container release tags
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "v1.0.0")

app = Flask(__name__)
swagger = Swagger(app)

MODEL_PATH = Path(os.getenv("MODEL_PATH", "/models/model.joblib"))
PREPROCESSOR_PATH = Path(os.getenv("PREPROCESSOR_PATH", "/models/preprocessor.joblib"))
METADATA_PATH = Path(os.getenv("METADATA_PATH", "/models/model_metadata.json"))

DEFAULT_MODEL_URL = os.getenv(
    "DEFAULT_MODEL_URL",
    "https://github.com/doda25-team2/model-service/releases/latest/download/model.joblib"
)

DEFAULT_PREPROCESSOR_URL = os.getenv(
    "DEFAULT_PREPROCESSOR_URL",
    "https://github.com/doda25-team2/model-service/releases/latest/download/preprocessor.joblib"
)

DEFAULT_METADATA_URL = os.getenv(
    "DEFAULT_METADATA_URL",
    "https://github.com/doda25-team2/model-service/releases/latest/download/model_metadata.json"
)

# Store loaded model metadata
model_metadata = None


def download_if_missing(local_path: Path, url: str, required: bool = True):
    """Download a file from URL if it doesn't exist locally."""
    if local_path.exists():
        return True
    
    print(f"{local_path} missing → downloading from {url}")
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        r = requests.get(url)
        r.raise_for_status()
        local_path.write_bytes(r.content)
        print(f"Downloaded: {local_path}")
        return True
    except requests.RequestException as e:
        if required:
            raise
        print(f"Warning: Could not download {url}: {e}")
        return False


def load_metadata():
    """Load model metadata from JSON file."""
    global model_metadata
    
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, 'r') as f:
                model_metadata = json.load(f)
            print(f"Loaded model metadata: {model_metadata.get('model_version', 'unknown')}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load metadata: {e}")
            model_metadata = None
    else:
        print("No model metadata file found")
        model_metadata = None


def parse_version(version_str: str) -> tuple:
    """Parse a version string like 'v1.2.3' or 'Model-v1.2.3' into a tuple (1, 2, 3)."""
    # Remove prefixes
    v = version_str.replace("Model-", "").lstrip("v")
    parts = v.split(".")
    return tuple(int(p) for p in parts[:3])


def check_compatibility():
    """Check if the loaded model is compatible with this service version."""
    if model_metadata is None:
        print("Warning: No metadata available, skipping compatibility check")
        return True
    
    compatibility = model_metadata.get("compatibility", {})
    min_service_version = compatibility.get("min_service_version")
    
    if min_service_version:
        try:
            min_version = parse_version(min_service_version)
            current_version = parse_version(SERVICE_VERSION)
            
            if current_version < min_version:
                print(f"Warning: Model requires service version >= {min_service_version}, "
                      f"but running {SERVICE_VERSION}")
                return False
            else:
                print(f"Compatibility check passed: service {SERVICE_VERSION} >= {min_service_version}")
        except (ValueError, IndexError) as e:
            print(f"Warning: Could not parse versions for compatibility check: {e}")
    
    return True


def ensure_model_available():
    """Download model files if not present locally."""
    download_if_missing(MODEL_PATH, DEFAULT_MODEL_URL, required=True)
    download_if_missing(PREPROCESSOR_PATH, DEFAULT_PREPROCESSOR_URL, required=True)
    download_if_missing(METADATA_PATH, DEFAULT_METADATA_URL, required=False)


# Initialize on module load
ensure_model_available()
load_metadata()
check_compatibility()

model = joblib.load(MODEL_PATH)
preprocessor = joblib.load(PREPROCESSOR_PATH)


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint with version information.
    ---
    responses:
      200:
        description: Service health status with version information
        schema:
          type: object
          properties:
            status:
              type: string
              example: healthy
            service_version:
              type: string
              example: v1.0.0
            model_version:
              type: string
              example: Model-v1.0.0
            model_accuracy:
              type: number
              example: 0.9456
            compatibility:
              type: object
    """
    response = {
        "status": "healthy",
        "service_version": SERVICE_VERSION,
        "model_version": model_metadata.get("model_version", "unknown") if model_metadata else "unknown",
        "model_loaded": model is not None and preprocessor is not None
    }
    
    if model_metadata:
        response["model_accuracy"] = model_metadata.get("performance", {}).get("accuracy")
        response["model_trained_at"] = model_metadata.get("trained_at")
        response["model_commit"] = model_metadata.get("training_commit")
        response["compatibility"] = model_metadata.get("compatibility", {})
    
    return jsonify(response)


@app.route('/version', methods=['GET'])
def version():
    """
    Get detailed version information.
    ---
    responses:
      200:
        description: Detailed version information for service and model
        schema:
          type: object
    """
    response = {
        "service": {
            "version": SERVICE_VERSION
        },
        "model": model_metadata if model_metadata else {"version": "unknown"}
    }
    return jsonify(response)


@app.route('/predict', methods=['POST'])
def predict():
    """
    Predict whether an SMS is Spam.
    ---
    consumes:
      - application/json
    parameters:
        - name: input_data
          in: body
          description: message to be classified.
          required: True
          schema:
            type: object
            required: sms
            properties:
                sms:
                    type: string
                    example: This is an example of an SMS.
    responses:
      200:
        description: "The result of the classification: 'spam' or 'ham'."
    """
    input_data = request.get_json()
    sms = input_data.get('sms')
    processed_sms = preprocessor.transform([sms])
    prediction = model.predict(processed_sms)[0]
    
    res = {
        "result": prediction,
        "classifier": "decision tree",
        "sms": sms,
        "service_version": SERVICE_VERSION,
        "model_version": model_metadata.get("model_version", "unknown") if model_metadata else "unknown"
    }
    print(res)
    return jsonify(res)


if __name__ == '__main__':
    # Read port from environment so container runtime can override it
    port = int(os.getenv("MODEL_SERVICE_PORT", "8081"))
    app.run(host="0.0.0.0", port=port, debug=True)
