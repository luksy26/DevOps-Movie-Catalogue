from flask import Flask, jsonify, request
import psycopg2
import jwt
import datetime
from psycopg2 import sql, OperationalError
import os
import bcrypt
import base64
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Database configuration (read from environment variables)
DB_HOST = os.environ.get("PGHOST", "postgres")
DB_USER = os.environ.get("PGUSER", "admin")
DB_PASSWORD = os.environ.get("PGPASSWORD", "admin")
DB_NAME = os.environ.get("PGDATABASE", "movieApp")
JWT_SECRET = "my_secret_key"  # ideally envv in prod

# Function to establish a database connection
def get_db_connection():
    connection_params = {
        "host": DB_HOST,
        "port": 5432,
        "database": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }
    try:
        conn = psycopg2.connect(**connection_params)
        return conn, None  # Connection succeeded, return it
    except OperationalError as e:
        return None, {"error": f"Error connecting to the database: {str(e)}", "parameters": connection_params}

# Function to test the database connection and initialize tables
def initialize_tables():
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # Create `users` table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL
                )
            """)

            # Create `movies` table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    genre VARCHAR(100) NOT NULL,
                    year INT NOT NULL
                )
            """)

            conn.commit()  # Save changes
            cur.close()
        finally:
            conn.close()

# Route to test the database connection and create tables
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

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Hash password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Base64 encode the bcrypt hash before storing in the database
    encoded_hash = base64.b64encode(hashed_password).decode('utf-8')

    # Save user to the database
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (username, password)
                VALUES (%s, %s)
                RETURNING id, username
            """, (username, encoded_hash))
            user = cur.fetchone()
            conn.commit()
            cur.close()
            return jsonify({"message": "User registered successfully", "user": {"id": user[0], "username": user[1], "encoded_hash": encoded_hash}}), 201
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
            cur.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
            user = cur.fetchone()

            # Retrieve the encoded hash from the database
            encoded_hash_from_db = user[2]  # assuming user[2] is the password column

            # Decode the base64 hash
            decoded_hash = base64.b64decode(encoded_hash_from_db)

            cur.close()

            if user and bcrypt.checkpw(password.encode('utf-8'), decoded_hash):
                # Password match, generate JWT token
                payload = {
                    "user_id": user[0],
                    "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)  # Token expiry
                }
                token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
                return jsonify({"token": token}), 200
            else:
                return jsonify({"error": "Invalid credentials"}), 401
        except psycopg2.Error as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            conn.close()

    return jsonify(error_info), 500

# Protected Route (Token Validation)
@app.route('/auth/protected', methods=['GET'])
def protected():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Token is missing"}), 401
    
    logging.debug(f"Token received in auth.py: {token}")  # Log the token

    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return jsonify({"message": "This is protected data", "user_id": decoded_token['user_id']}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

if __name__ == '__main__':
    initialize_tables()
    app.run(debug=True, host='0.0.0.0', port=5000)
