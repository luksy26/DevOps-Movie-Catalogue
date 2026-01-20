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

# Function to initialize reviews table
def initialize_table():
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # Create `reviews` table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    id SERIAL PRIMARY KEY,
                    movie_id INT NOT NULL,
                    user_id INT NOT NULL,
                    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    review_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(movie_id, user_id)
                )
                """
            )

            conn.commit()  # Save changes
            cur.close()
            logging.info("✅ Reviews table initialized successfully")
            return True
        except Exception as e:
            logging.error(f"❌ Error initializing reviews table: {e}")
            return False
        finally:
            conn.close()
    else:
        logging.error(f"❌ Database connection failed: {error_info}")
    return False

# Route to test the database connection
@app.route('/reviews/test-db', methods=['GET'])
def test_db_connection():
    conn, error_info = get_db_connection()
    if conn:
        conn.close()
        return jsonify({"message": "Review service: Database connected."}), 200
    # If connection failed, return debug info
    return jsonify(error_info), 500

# Submit or update a movie review
@app.route('/reviews', methods=['POST'])
def submit_review():
    """
    Submit or update a review for a movie
    Input: { "movie_id": 123, "user_id": 456, "rating": 4, "review_text": "Great movie!" }
    """
    data = request.get_json()
    movie_id = data.get('movie_id')
    user_id = data.get('user_id')
    rating = data.get('rating')
    review_text = data.get('review_text', '')

    # Validation
    if not movie_id or not user_id or not rating:
        return jsonify({"error": "movie_id, user_id, and rating are required"}), 400
    
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be an integer between 1 and 5"}), 400

    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # Check if movie exists in allMovies
            cur.execute("SELECT id FROM allMovies WHERE id = %s", (movie_id,))
            if not cur.fetchone():
                cur.close()
                conn.close()
                return jsonify({"error": "Movie not found"}), 404

            # Insert or update review (UPSERT)
            cur.execute(
                """
                INSERT INTO reviews (movie_id, user_id, rating, review_text)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (movie_id, user_id)
                DO UPDATE SET
                    rating = EXCLUDED.rating,
                    review_text = EXCLUDED.review_text,
                    created_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (movie_id, user_id, rating, review_text)
            )
            
            review_id = cur.fetchone()[0]

            # Recalculate average rating for the movie
            cur.execute(
                """
                SELECT AVG(rating)::FLOAT, COUNT(*)
                FROM reviews
                WHERE movie_id = %s
                """,
                (movie_id,)
            )
            avg_rating, review_count = cur.fetchone()

            # Update movie's average rating
            cur.execute(
                """
                UPDATE allMovies
                SET avg_rating = %s, review_count = %s
                WHERE id = %s
                """,
                (avg_rating or 0.0, review_count or 0, movie_id)
            )

            conn.commit()
            cur.close()

            return jsonify({
                "message": "Review submitted successfully",
                "review_id": review_id,
                "new_avg_rating": round(avg_rating, 2) if avg_rating else 0.0,
                "total_reviews": review_count
            }), 201

        except psycopg2.Error as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            conn.close()

    return jsonify(error_info), 500

# Get reviews for a movie
@app.route('/reviews/<int:movie_id>', methods=['GET'])
def get_movie_reviews(movie_id):
    """
    Get all reviews for a specific movie
    """
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # Get movie info with rating
            cur.execute(
                """
                SELECT id, name, avg_rating, review_count
                FROM allMovies
                WHERE id = %s
                """,
                (movie_id,)
            )
            movie = cur.fetchone()

            if not movie:
                cur.close()
                conn.close()
                return jsonify({"error": "Movie not found"}), 404

            # Get all reviews for this movie
            cur.execute(
                """
                SELECT id, user_id, rating, review_text, created_at
                FROM reviews
                WHERE movie_id = %s
                ORDER BY created_at DESC
                """,
                (movie_id,)
            )
            reviews = cur.fetchall()

            review_list = [
                {
                    "id": review[0],
                    "user_id": review[1],
                    "rating": review[2],
                    "review_text": review[3],
                    "created_at": review[4].isoformat() if review[4] else None
                }
                for review in reviews
            ]

            cur.close()
            return jsonify({
                "movie": {
                    "id": movie[0],
                    "name": movie[1],
                    "avg_rating": round(movie[2], 2) if movie[2] else 0.0,
                    "review_count": movie[3]
                },
                "reviews": review_list
            }), 200

        except psycopg2.Error as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            conn.close()

    return jsonify(error_info), 500

if __name__ == '__main__':
    import time
    logging.info("🔄 Trying to initialize 'reviews' table in database...")
    max_retries = 30
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        if initialize_table():
            logging.info("✅ Reviews table created in database.")
            break
        logging.warning(f"⚠️  Database not ready, retrying... (attempt {attempt + 1}/{max_retries})")
        time.sleep(retry_delay)
    else:
        logging.error("❌ Failed to initialize database after maximum retries. Starting app anyway...")
    
    app.run(debug=True, host='0.0.0.0', port=8093)
