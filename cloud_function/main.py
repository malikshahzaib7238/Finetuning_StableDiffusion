import functions_framework
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from flask import Flask, jsonify, send_file
import requests
from flask_cors import CORS
import os


app = Flask(__name__)
CORS(app)


key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")


try:
    credentials = service_account.Credentials.from_service_account_file(
        key_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    access_token = credentials.token
except Exception as e:
    print(f"Error loading credentials: {e}")
    access_token = None


def predict_custom_trained_model_sample(project, endpoint_id, location, instances):
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/endpoints/{endpoint_id}:predict"
    payload = {"instances": [instances]}
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {access_token}"}

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


@functions_framework.http
@app.route('/', methods=['GET', 'POST'])
def serve(request):
    if request.method == 'POST':
        try:
            print("Received request to generate image.")
            data = request.get_json()
            if not data:
                print("Invalid JSON received.")
                return jsonify({"error": "Invalid JSON provided"}), 400

            prompt = data.get('prompt')
            if not prompt:
                app.logger.warning("No prompt provided in the request.")
                return jsonify({"error": "No prompt provided"}), 400

            print(f"Prompt received: {prompt}")

            project = "651050524144"
            endpoint_id = "5144950257410375680"
            location = "us-central1"

            print("Calling prediction API...")
            prediction = predict_custom_trained_model_sample(
                project, endpoint_id, location, prompt)

            if prediction:
                base64_image = prediction.get('predictions', [None])[0]
                if base64_image:
                    app.logger.info("Image generated successfully.")
                    return jsonify({"image": base64_image})
                else:
                    print("No image data received in prediction response.")
                    return jsonify({"error": "No image data in response"}), 500
            else:
                print("Prediction API call failed, no response received.")
                return jsonify({"error": "Failed to generate image"}), 500
        except Exception as e:

            print(f"An error occurred while generating image: {e}")
            return jsonify({"error": "An unexpected error occurred"}), 500

    return send_file('index.html')


if __name__ == '__main__':
    app.run()
