from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Authentication Service URL
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth:8090")

@app.route('/api/testauth', methods=['GET'])
def api_testauth():
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/auth/test-db", timeout=5)
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
        response = requests.post(f"{AUTH_SERVICE_URL}/auth/register", json=data, timeout=5)
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
        response = requests.post(f"{AUTH_SERVICE_URL}/auth/login", json=data, timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to auth service",
                "details": str(e)
            }
            ), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """
    Logout a user. Marks their session as inactive.
    """
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Authorization token required"}), 401

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/auth/logout",
            headers={"Authorization": token},
            timeout=5
        )
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
            headers={"Authorization": token},
            timeout=5
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
    import time
    start_time = time.time()
    logging.info(f"[TIMING] api get_movies started")
    
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"message": "Token is missing"}), 401
    try:
        logging.info(f"[TIMING] Before auth call: {time.time() - start_time:.3f}s")
        response = requests.get(
            f"{AUTH_SERVICE_URL}/auth/movies",
            headers={"Authorization": token},
            timeout=5
        )
        logging.info(f"[TIMING] After auth call: {time.time() - start_time:.3f}s")
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
            json=data,
            timeout=5
            )
        if response.status_code == 201:
            # If token is valid, perform business logic or call another pod
            return jsonify(
                {
                    "message": "Token is valid", 
                    "Added movie": response.json()
                 }
                ), response.status_code
        elif response.status_code == 409:
            # Duplicate movie - pass through the error message
            return jsonify(response.json()), 409
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
            json=data,
            timeout=5
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

@app.route('/api/all-movies', methods=['GET'])
def get_all_movies():
    """
    Get all movies from the master catalogue.
    Public endpoint - no authentication required.
    """
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/auth/all-movies", timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to auth service",
                "details": str(e)
            }
        ), 500

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """
    Get movie recommendations based on selected genres.
    Public endpoint - no authentication required.
    """
    data = request.get_json()
    try:
        response = requests.post(f"{AUTH_SERVICE_URL}/auth/recommendations", json=data, timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to auth service",
                "details": str(e)
            }
        ), 500

@app.route('/api/reviews', methods=['POST'])
def submit_review():
    """
    Submit a review for a movie. Requires authentication.
    """
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"message": "Token is missing"}), 401

    data = request.get_json()
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/auth/reviews",
            headers={"Authorization": token},
            json=data,
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to auth service",
                "details": str(e)
            }
        ), 500

@app.route('/api/reviews/<int:movie_id>', methods=['GET'])
def get_movie_reviews(movie_id):
    """
    Get reviews for a movie. Public endpoint.
    """
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/auth/reviews/{movie_id}", timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to auth service",
                "details": str(e)
            }
        ), 500

# =====================================================
# NOTIFICATION ENDPOINTS
# =====================================================

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """
    Get notifications for the authenticated user
    """
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Authorization token required"}), 401

    try:
        response = requests.get(
            f"{AUTH_SERVICE_URL}/auth/notifications",
            headers={"Authorization": token},
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to auth service",
                "details": str(e)
            }
        ), 500

@app.route('/api/notifications/unread-count', methods=['GET'])
def get_unread_count():
    """
    Get count of unread notifications for the authenticated user
    """
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Authorization token required"}), 401

    try:
        response = requests.get(
            f"{AUTH_SERVICE_URL}/auth/notifications/unread-count",
            headers={"Authorization": token},
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to auth service",
                "details": str(e)
            }
        ), 500

@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id):
    """
    Mark a notification as read
    """
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Authorization token required"}), 401

    try:
        response = requests.put(
            f"{AUTH_SERVICE_URL}/auth/notifications/{notification_id}/read",
            headers={"Authorization": token},
            timeout=5
        )
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