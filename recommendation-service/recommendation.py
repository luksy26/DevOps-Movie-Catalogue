from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2 import OperationalError
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database configuration (read from environment variables)
DB_HOST = os.environ.get("PGHOST", "postgres")
DB_HOSTADDR = os.environ.get("PGHOSTADDR")  # IP address to bypass DNS
DB_USER = os.environ.get("PGUSER", "admin")
DB_PASSWORD = os.environ.get("PGPASSWORD", "admin")
DB_NAME = os.environ.get("PGDATABASE", "movieApp")

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

# Route to test the database connection
@app.route('/recommendations/test-db', methods=['GET'])
def test_db_connection():
    conn, error_info = get_db_connection()
    if conn:
        conn.close()
        return jsonify({"message": "Recommendation service: Database connected."}), 200
    # If connection failed, return debug info
    return jsonify(error_info), 500

# Get movie recommendations based on genres
@app.route('/recommendations', methods=['POST'])
def get_recommendations():
    """
    Get movie recommendations based on selected genres and popularity
    Input: { "genres": ["Action", "Comedy", "Drama"], "limit": 10 }
    Output: List of movies from those genres, sorted by popularity
    """
    data = request.get_json()
    genres = data.get('genres', [])
    limit = data.get('limit', 20)  # Default to top 20 recommendations

    if not genres or not isinstance(genres, list):
        return jsonify(
            {
                "error": "Genres array is required"
            }
        ), 400

    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # Build query to get movies matching any of the selected genres
            # Use parameterized query to prevent SQL injection
            placeholders = ', '.join(['%s'] * len(genres))
            query = f"""
                SELECT id, name, genre, year, popularity, avg_rating, review_count
                FROM allMovies
                WHERE genre IN ({placeholders})
                ORDER BY popularity DESC
                LIMIT %s
            """
            
            cur.execute(query, (*genres, limit))
            movies = cur.fetchall()
            
            logging.info(f"Found {len(movies)} recommendations for genres: {genres}")

            if not movies:
                return jsonify(
                    {
                        "message": "No recommendations found for selected genres",
                        "recommendations": []
                    }
                ), 200

            # Format the movie list
            recommendations = [
                {
                    "id": movie[0],
                    "name": movie[1], 
                    "genre": movie[2], 
                    "year": movie[3],
                    "popularity": movie[4],
                    "avg_rating": round(movie[5], 1) if movie[5] else 0.0,
                    "review_count": movie[6] or 0
                } 
                for movie in movies
            ]

            cur.close()
            return jsonify({"recommendations": recommendations}), 200
            
        except psycopg2.Error as e:
            return jsonify({"error": f"Error fetching recommendations: {str(e)}"}), 500
        finally:
            conn.close()

    return jsonify(error_info), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8092)
