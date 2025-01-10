from flask import Flask, request, jsonify
import requests
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Authentication Service URL
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth:8090")

@app.route('/api/testauth', methods=['GET'])
def api_testauth():
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/auth/test-db")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Unable to connect to auth service", "details": str(e)}), 500

@app.route('/api/register', methods=['POST'])
def api_register():
    """
    Register a new user. This forwards the request to the authentication service.
    """
    data = request.get_json()
    try:
        # Forward registration to the authentication service
        response = requests.post(f"{AUTH_SERVICE_URL}/auth/register", json=data)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Unable to connect to auth service", "details": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    """
    Login a user. This forwards the request to the authentication service.
    """
    data = request.get_json()
    try:
        # Forward login request to the authentication service
        response = requests.post(f"{AUTH_SERVICE_URL}/auth/login", json=data)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Unable to connect to auth service", "details": str(e)}), 500

@app.route('/api/protected', methods=['GET'])
def api_protected():
    """
    Example of a protected route requiring token authentication.
    """
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"message": "Token is missing"}), 401

    logging.debug(f"Token received in api.py: {token}")  # Log the token

    # Forward the token to the authentication service for validation
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/auth/protected", headers={"Authorization": token})
        if response.status_code == 200:
            # If token is valid, perform business logic or call another pod
            return jsonify({"message": "Token is valid", "data": response.json()}), 200
        else:
            return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Unable to connect to auth service", "details": str(e)}), 500
    
@app.route('/api/business-logic', methods=['GET'])
def business_logic():
    """
    Placeholder for a future business logic route.
    """
    return jsonify({"message": "Business logic route placeholder"}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)