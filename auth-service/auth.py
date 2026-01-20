from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import psycopg2
import jwt
import datetime
from psycopg2 import OperationalError
import os
import bcrypt
import base64
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Service URLs
CATALOGUE_SERVICE_URL = os.environ.get(
    "CATALOGUE_SERVICE_URL",
    "http://catalogue:8091"
    )
RECOMMENDATION_SERVICE_URL = os.environ.get(
    "RECOMMENDATION_SERVICE_URL",
    "http://recommendation-service:8092"
    )
REVIEW_SERVICE_URL = os.environ.get(
    "REVIEW_SERVICE_URL",
    "http://review-service:8093"
    )
NOTIFICATION_SERVICE_URL = os.environ.get(
    "NOTIFICATION_SERVICE_URL",
    "http://notification-service:8094"
    )

# Database configuration (read from environment variables)
DB_HOST = os.environ.get("PGHOST", "postgres")
DB_HOSTADDR = os.environ.get("PGHOSTADDR")  # IP address to bypass DNS
DB_USER = os.environ.get("PGUSER", "admin")
DB_PASSWORD = os.environ.get("PGPASSWORD", "admin")
DB_NAME = os.environ.get("PGDATABASE", "movieApp")
JWT_SECRET = "my_secret_key"  # ideally envv in prod

# Function to establish a database connection
def get_db_connection():
    connection_params = {
        "port": 5432,
        "database": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }
    
    # Use IP address if provided to bypass DNS resolution
    if DB_HOSTADDR:
        connection_params["host"] = DB_HOSTADDR
    else:
        connection_params["host"] = DB_HOST
    
    try:
        conn = psycopg2.connect(**connection_params)
        return conn, None
    except OperationalError as e:
        return None, {"error": f"Error connecting to database: {str(e)}"}
    except Exception as e:
        return None, {"error": f"Error: {str(e)}"}

# Function to initialize 'users't able in the database
def initialize_table():
    conn, _ = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # Create `users` table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(255)
                )
                """
            )

            conn.commit()  # Save changes
            cur.close()
            return True
        finally:
            conn.close()
    return False


# Route to test the database connection
@app.route('/auth/test-db', methods=['GET'])
def test_db_connection():
    conn, error_info = get_db_connection()
    if conn:
        return jsonify({"message": "Database connected."}), 200
    # If connection failed, return debug info
    return jsonify(error_info), 500

# User Registration
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')  # Optional email

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Check if user already exists
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Check if username already exists
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            existing_user = cur.fetchone()

            if existing_user:
                return jsonify({"error": "Username already exists"}), 400

            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # Base64 encode the bcrypt hash before storing in the database
            encoded_hash = base64.b64encode(hashed_password).decode('utf-8')

            # Save user to the database
            cur.execute("""
                INSERT INTO users (username, password, email)
                VALUES (%s, %s, %s)
                RETURNING id, username, email
            """, (username, encoded_hash, email))
            user = cur.fetchone()
            conn.commit()
            cur.close()

            return jsonify(
                {
                    "message": "User registered successfully",
                    "user": 
                        {
                            "id": user[0],
                            "username": user[1],
                            "encoded_hash": encoded_hash
                        }
                }
            ), 201
        except psycopg2.Error as e:
            return jsonify({"error": f"Error inserting user: {str(e)}"}), 500
        finally:
            conn.close()

    return jsonify(error_info), 500

# User Login
@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Retrieve user from database
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, password, email FROM users WHERE username = %s",
                (username,)
            )
            user = cur.fetchone()

            logging.debug(f"Row for {username} in the database is {user}")
            
            # Handle case when user does not exist
            if not user:
                return jsonify({"error": "User does not exist"}), 404

            # Retrieve the encoded hash from the database
            encoded_hash_from_db = user[2]  # user[2] is the password column
            user_email = user[3] if len(user) > 3 else None  # user[3] is the email column

            # Decode the base64 hash
            decoded_hash = base64.b64decode(encoded_hash_from_db)

            cur.close()

            if user and bcrypt.checkpw(password.encode('utf-8'), decoded_hash):
                # Password match, generate JWT token
                user_id = user[0]
                payload = {
                    "user_id": user_id,
                    "exp": datetime.datetime.now(datetime.timezone.utc) 
                            + datetime.timedelta(hours=1)  # Token expiry
                }
                token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
                
                # Register user session with notification service (including email)
                try:
                    session_data = {"user_id": user_id}
                    if user_email:
                        session_data["user_email"] = user_email
                    
                    session_response = requests.post(
                        f"{NOTIFICATION_SERVICE_URL}/notifications/session",
                        json=session_data,
                        timeout=2
                    )
                    if session_response.status_code == 200:
                        email_info = f" ({user_email})" if user_email else ""
                        logging.info(f"✅ User session registered with notification service: {user_id}{email_info}")
                    else:
                        logging.warning(f"⚠️  Failed to register session: {session_response.status_code}")
                except Exception as e:
                    logging.error(f"⚠️  Could not reach notification service: {e}")
                
                return jsonify({"token": token}), 200
            else:
                return jsonify({"error": "Invalid credentials"}), 401
        except psycopg2.Error as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            conn.close()

    return jsonify(error_info), 500

@app.route('/auth/logout', methods=['POST'])
def logout():
    """Logout user and mark session as inactive"""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Token is missing"}), 401

    try:
        # Decode token to get user_id
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')
        
        # Mark session as inactive in notification service
        try:
            session_response = requests.delete(
                f"{NOTIFICATION_SERVICE_URL}/notifications/session/{user_id}",
                timeout=2
            )
            if session_response.status_code == 200:
                logging.info(f"✅ User session ended: {user_id}")
            else:
                logging.warning(f"⚠️  Failed to end session: {session_response.status_code}")
        except Exception as e:
            logging.error(f"⚠️  Could not reach notification service: {e}")
        
        return jsonify({"message": "Logged out successfully"}), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

@app.route('/auth/movies', methods=['GET'])
def get_movies():
    import time
    start_time = time.time()
    logging.info(f"[TIMING] auth get_movies started")
    
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Token is missing"}), 401

    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        logging.info(f"[TIMING] After JWT decode: {time.time() - start_time:.3f}s")
        user_id = decoded_token.get('user_id')
        jsonData = {"user_id": user_id}
        logging.info(f"[TIMING] Before catalogue call: {time.time() - start_time:.3f}s")
        response = requests.get(
            f"{CATALOGUE_SERVICE_URL}/catalogue/movies",
            json=jsonData,
            timeout=5
        )
        logging.info(f"[TIMING] After catalogue call: {time.time() - start_time:.3f}s")
        logging.debug("Response from catalogue is: " + response.text)
        return jsonify(response.json()), response.status_code
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    
@app.route('/auth/movies', methods=['POST'])
def add_movie():
    # Get the token from Authorization header
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Token is missing"}), 401

    # Get movie data from the request body
    data = request.get_json()
    name = data.get('name')
    genre = data.get('genre')
    year = data.get('year')

    if not name or not genre or not year:
        return jsonify(
            {
                "error": "All fields (name, genre, year) are required"
            }
        ), 400

    try:
        # Decode the token
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')

        # Prepare data to send to the catalogue service
        jsonData = {
            "user_id": user_id,
            "name": name,
            "genre": genre,
            "year": year
        }

        # Send POST request to the catalogue service to add the movie
        response = requests.post(
            f"{CATALOGUE_SERVICE_URL}/catalogue/movies",
            json=jsonData,
            timeout=5
        )

        # Return the response from the catalogue service
        if response.status_code == 201:  # If successful
            return jsonify(response.json()), 201
        elif response.status_code == 409:  # Duplicate movie
            return jsonify(response.json()), 409
        else:
            return jsonify(
                {
                    "error": "Failed to add movie",
                    "details": response.json()
                }
            ), 500

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/auth/movies', methods=['DELETE'])
def delete_movie():
    # Get the token from Authorization header
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Token is missing"}), 401

    # Get movie data from the request body
    data = request.get_json()
    name = data.get('name')
    year = data.get('year')

    if not name or not year:
        return jsonify({"error": "Both name and year are required"}), 400

    try:
        # Decode the token
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')

        # Prepare data to send to the catalogue service
        jsonData = {
            "user_id": user_id,
            "name": name,
            "year": year
        }

        # Send DELETE request to the catalogue service to delete the movie
        response = requests.delete(
            f"{CATALOGUE_SERVICE_URL}/catalogue/movies",
            json=jsonData,
            timeout=5
        )

        # Return the response from the catalogue service
        if response.status_code == 200:  # If successful
            return jsonify(response.json()), 200
        elif response.status_code == 404:  # If movie not found
            return jsonify({"error": "Movie not found"}), 404
        else:
            return jsonify(
                {
                    "error": "Failed to delete movie",
                    "details": response.json()
                }
            ), 500

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Protected Route Test (Token Validation)
@app.route('/auth/protected', methods=['GET'])
def protected():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Token is missing"}), 401
    
    logging.debug(f"Token received in auth.py: {token}")  # Log the token

    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return jsonify(
            {
                "message": "This is protected data",
                "user_id": decoded_token['user_id']
            }
        ), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

@app.route('/auth/all-movies', methods=['GET'])
def get_all_movies():
    """
    Get all movies from the master catalogue.
    No authentication required - public catalogue.
    """
    try:
        response = requests.get(
            f"{CATALOGUE_SERVICE_URL}/catalogue/all-movies",
            timeout=5
        )
        logging.debug("Response from catalogue/all-movies: " + response.text)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to catalogue service",
                "details": str(e)
            }
        ), 500

@app.route('/auth/recommendations', methods=['POST'])
def get_recommendations():
    """
    Get movie recommendations based on selected genres.
    No authentication required - public recommendations.
    """
    data = request.get_json()
    
    try:
        response = requests.post(
            f"{RECOMMENDATION_SERVICE_URL}/recommendations",
            json=data,
            timeout=5
        )
        logging.debug("Response from recommendation service: " + response.text)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to recommendation service",
                "details": str(e)
            }
        ), 500

@app.route('/auth/reviews', methods=['POST'])
def submit_review():
    """
    Submit a review for a movie. Requires authentication.
    """
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Token is missing"}), 401

    try:
        # Decode token to get user_id
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')

        # Get review data and add user_id
        data = request.get_json()
        data['user_id'] = user_id

        # Forward to review service
        response = requests.post(
            f"{REVIEW_SERVICE_URL}/reviews",
            json=data,
            timeout=5
        )
        return jsonify(response.json()), response.status_code

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to review service",
                "details": str(e)
            }
        ), 500

@app.route('/auth/reviews/<int:movie_id>', methods=['GET'])
def get_movie_reviews(movie_id):
    """
    Get reviews for a movie. No authentication required.
    """
    try:
        response = requests.get(
            f"{REVIEW_SERVICE_URL}/reviews/{movie_id}",
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to review service",
                "details": str(e)
            }
        ), 500

# =====================================================
# NOTIFICATION SERVICE ENDPOINTS
# =====================================================

@app.route('/auth/notifications', methods=['GET'])
def get_user_notifications():
    """
    Get notifications for the authenticated user
    """
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Token is missing"}), 401

    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')

        # Forward to notification service
        response = requests.get(
            f"{NOTIFICATION_SERVICE_URL}/notifications/{user_id}",
            timeout=5
        )
        return jsonify(response.json()), response.status_code

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to notification service",
                "details": str(e)
            }
        ), 500

@app.route('/auth/notifications/unread-count', methods=['GET'])
def get_unread_notification_count():
    """
    Get count of unread notifications for the authenticated user
    """
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Token is missing"}), 401

    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')

        # Forward to notification service
        response = requests.get(
            f"{NOTIFICATION_SERVICE_URL}/notifications/{user_id}/unread-count",
            timeout=5
        )
        return jsonify(response.json()), response.status_code

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to notification service",
                "details": str(e)
            }
        ), 500

@app.route('/auth/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_as_read(notification_id):
    """
    Mark a notification as read
    """
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Token is missing"}), 401

    try:
        # Verify token
        jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

        # Forward to notification service
        response = requests.put(
            f"{NOTIFICATION_SERVICE_URL}/notifications/{notification_id}/read",
            timeout=5
        )
        return jsonify(response.json()), response.status_code

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "error": "Unable to connect to notification service",
                "details": str(e)
            }
        ), 500

if __name__ == '__main__':
    logging.debug("Trying to initialize 'users' table in database...")
    while not initialize_table():
        pass
    logging.debug("'users' table created in database.")
    app.run(debug=True, host='0.0.0.0', port=5000)
