from flask import Flask, jsonify, request
import psycopg2
from psycopg2 import OperationalError
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Database configuration (read from environment variables)
DB_HOST = os.environ.get("PGHOST", "postgres")
DB_USER = os.environ.get("PGUSER", "admin")
DB_PASSWORD = os.environ.get("PGPASSWORD", "admin")
DB_NAME = os.environ.get("PGDATABASE", "movieApp")

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
        return None, {
            "error": 
                f"Error connecting to the database: {str(e)}", 
                "parameters": connection_params
            }

# Function to initialize 'movies' table in the database
def initialize_table():
    conn, _ = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # Create `movies` table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS movies (
                    id SERIAL PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    genre VARCHAR(100) NOT NULL,
                    year INT NOT NULL
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
@app.route('/catalogue/test-db', methods=['GET'])
def test_db_connection():
    conn, error_info = get_db_connection()
    if conn:
        return jsonify({"message": "Database connected."}), 200
    # If connection failed, return debug info
    return jsonify(error_info), 500

# Get Movie list for a user
@app.route('/catalogue/movies', methods=['GET'])
def get_movies():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify(
            {
                "error": "User_id for the movie list is required"
            }
        ), 400

    # Get movies for the given user from the database
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # Fetch movies associated with the user ID
            cur.execute(
                """
                SELECT name, genre, year
                FROM movies
                WHERE user_id = %s
                """,
                (user_id,)
            )

            movies = cur.fetchall()
            logging.debug(movies)


            if not movies:
                return jsonify(
                    {
                        "message": "No movies found for this user"
                    }
                ), 200

            # Format the movie list
            movie_list = [
                {
                    "name": movie[0], 
                    "genre": movie[1], 
                    "year": movie[2]
                } 
                for movie in movies
            ]

            cur.close()
            return jsonify({"movies": movie_list}), 200
        except psycopg2.Error as e:
            return jsonify({"error": f"Error fetching movies: {str(e)}"}), 500
        finally:
            conn.close()

    return jsonify(error_info), 500

@app.route('/catalogue/movies', methods=['POST'])
def add_movie():
    data = request.get_json()
    user_id = data.get('user_id')
    name = data.get('name')
    genre = data.get('genre')
    year = data.get('year')

    if not user_id or not name or not genre or not year:
        return jsonify(
            {
                "error": "All fields (user_id, name, genre, year) are required"
            }
        ), 400

    # Insert the new movie for the user into the movies table
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # Insert new movie for the user_id
            cur.execute(
                """
                INSERT INTO movies (user_id, name, genre, year)
                VALUES (%s, %s, %s, %s)
                RETURNING id, name, genre, year
                """,
                (user_id, name, genre, year)
            )

            new_movie = cur.fetchone()
            conn.commit()  # Save changes
            cur.close()

            return jsonify(
                {
                    "message": "Movie added successfully",
                    "movie": {
                        "id": new_movie[0],
                        "name": new_movie[1],
                        "genre": new_movie[2],
                        "year": new_movie[3]
                    }
                }
            ), 201
        except psycopg2.Error as e:
            return jsonify({"error": f"Error adding movie: {str(e)}"}), 500
        finally:
            conn.close()

    return jsonify(error_info), 500

@app.route('/catalogue/movies', methods=['DELETE'])
def delete_movie():
    data = request.get_json()
    name = data.get('name')
    year = data.get('year')
    user_id = data.get('user_id')

    if not name or not year or not user_id:
        return jsonify(
            {
                "error": "Both name, year and user_id are required"
            }
        ), 400

    # Establish database connection
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # Check if the movie exists
            cur.execute(
                "SELECT id FROM movies "
                "WHERE name = %s AND year = %s AND user_id = %s",
                (name, year, user_id)
            )
            movie = cur.fetchone()

            if not movie:
                return jsonify({"error": "Movie not found"}), 404

            # Delete the movie
            cur.execute(
                "DELETE FROM movies "
                "WHERE name = %s AND year = %s AND user_id = %s",
                (name, year, user_id)
            )
            conn.commit()
            cur.close()

            return jsonify({"message": "Movie deleted successfully"}), 200
        except psycopg2.Error as e:
            return jsonify({"error": f"Error deleting movie: {str(e)}"}), 500
        finally:
            conn.close()

    return jsonify(error_info), 500

if __name__ == '__main__':
    logging.debug("Trying to initialize 'movies' table in database...")
    while not initialize_table():
        pass
    logging.debug("'movies' table created in database.")
    app.run(debug=True, host='0.0.0.0', port=5001)
