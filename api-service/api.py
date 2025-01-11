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
        return jsonify(
            {
                "error": "Unable to connect to auth service",
                "details": str(e)
            }
            ), 500

@app.route('/api/register', methods=['POST'])
def api_register():
    """
    Register a new user. This forwards the request to the auth service.
    """
    data = request.get_json()
    try:
        # Forward registration to the authentication service
        response = requests.post(f"{AUTH_SERVICE_URL}/auth/register", json=data)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to auth service",
                "details": str(e)
            }
            ), 500

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
        return jsonify(
            {
                "error": "Unable to connect to auth service",
                "details": str(e)
            }
            ), 500

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
        response = requests.get(
            f"{AUTH_SERVICE_URL}/auth/protected",
            headers={"Authorization": token}
            )
        if response.status_code == 200:
            # If token is valid, perform business logic or call another pod
            return jsonify(
                {
                    "message": "Token is valid",
                    "data": response.json()
                }
                ), 200
        else:
            return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to auth service",
                "details": str(e)
            }
            ), 500
    
@app.route('/api/movies', methods=['GET'])
def get_movies():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"message": "Token is missing"}), 401
    try:
        response = requests.get(
            f"{AUTH_SERVICE_URL}/auth/movies",
            headers={"Authorization": token}
        )
        logging.debug("Response has code: " + str(response.status_code))
        logging.debug("Response content: " + response.text)

        if response.status_code == 200:
            try:
                response_data = response.json()
                return jsonify(response_data), response.status_code
            except ValueError:
                logging.error("Error parsing response as JSON")
                return jsonify(
                    {
                        "error": "Invalid JSON response from auth service"
                    }
                ), 500

        else:
            return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to auth service",
                "details": str(e)
            }
        ), 500

@app.route('/api/movies', methods=['POST'])
def post_movie():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"message": "Token is missing"}), 401
    try:
        data = request.get_json()
        response = requests.post(
            f"{AUTH_SERVICE_URL}/auth/movies",
            headers={"Authorization": token},
            json=data
            )
        if response.status_code == 201:
            # If token is valid, perform business logic or call another pod
            return jsonify(
                {
                    "message": "Token is valid", 
                    "Added movie": response.json()
                 }
                ), response.status_code
        else:
            return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to auth service",
                "details": str(e)
            }
            ), 500
    
@app.route('/api/movies', methods=['DELETE'])
def delete_movie():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"message": "Token is missing"}), 401
    try:
        data = request.get_json()
        response = requests.delete(
            f"{AUTH_SERVICE_URL}/auth/movies",
            headers={"Authorization": token},
            json=data
        )
        if response.status_code == 200:
            return jsonify(
                {
                    "message": "Token is valid",
                    "Deleted movie": response.json()
                }
            ), response.status_code
        elif response.status_code == 404:
            return jsonify({"error": "Movie not found"}), 404
        else:
            return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to auth service",
                "details": str(e)
            }
        ), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)