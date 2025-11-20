"""
Flask API of the SMS Spam detection model model.
"""
#stdlib
#external
import joblib
from flask import Flask, jsonify, request
from flasgger import Swagger
import pandas as pd
#internal
from config import OUTPUT_PATH
from text_preprocessing import prepare, _extract_message_len, _text_process
import os
import requests
from pathlib import Path
import joblib

app = Flask(__name__)
swagger = Swagger(app)

MODEL_PATH = Path(os.getenv("MODEL_PATH", "/models/model.joblib"))
PREPROCESSOR_PATH = Path(os.getenv("PREPROCESSOR_PATH", "/models/preprocessor.joblib"))

DEFAULT_MODEL_URL = os.getenv(
    "DEFAULT_MODEL_URL",
    "https://github.com/doda25-team2/model-service/releases/latest/download/model.joblib"
)

DEFAULT_PREPROCESSOR_URL = os.getenv(
    "DEFAULT_PREPROCESSOR_URL",
    "https://github.com/doda25-team2/model-service/releases/latest/download/preprocessor.joblib"
)

def download_if_missing(local_path: Path, url: str):
    if local_path.exists():
        return
    print(f"{local_path} missing → downloading from {url}")

    local_path.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url)
    r.raise_for_status()
    local_path.write_bytes(r.content)

    print(f"Downloaded: {local_path}")


def ensure_model_available():
    download_if_missing(MODEL_PATH, DEFAULT_MODEL_URL)
    download_if_missing(PREPROCESSOR_PATH, DEFAULT_PREPROCESSOR_URL)

ensure_model_available()
model = joblib.load(MODEL_PATH)
preprocessor = joblib.load(PREPROCESSOR_PATH)

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
        "sms": sms
    }
    print(res)
    return jsonify(res)

if __name__ == '__main__':
  # Read port from environment so container runtime can override it
  import os
  # default to 8081 if MODEL_SERVICE_PORT is not set
  port = int(os.getenv("MODEL_SERVICE_PORT", "8081"))
  #clf = joblib.load(OUTPUT_PATH / 'model.joblib')
  app.run(host="0.0.0.0", port=port, debug=True)
