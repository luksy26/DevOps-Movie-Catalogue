from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2 import OperationalError
import os
import logging
import requests

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

# TMDB API configuration
TMDB_API_TOKEN = os.environ.get("TMDB_API_TOKEN", "")

# TMDB Genre ID to name mapping
GENRE_MAP = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Science Fiction",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western"
}

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

# Function to initialize tables in the database
def initialize_table():
    conn, _ = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # Create `userMovies` table (renamed from movies)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS userMovies (
                    id SERIAL PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    genre VARCHAR(100) NOT NULL,
                    year INT NOT NULL
                )
                """
            )

            # Create `allMovies` table (master catalogue)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS allMovies (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    genre VARCHAR(100) NOT NULL,
                    year INT NOT NULL,
                    popularity FLOAT DEFAULT 0.0,
                    avg_rating FLOAT DEFAULT 0.0,
                    review_count INT DEFAULT 0,
                    UNIQUE(name, year)
                )
                """
            )

            conn.commit()  # Save changes
            cur.close()
            return True
        finally:
            conn.close()
    return False

# Function to fetch movies from TMDB API and populate allMovies table
def populate_movies_from_tmdb():
    """
    Fetch popular movies from TMDB API (first 10 pages) and populate allMovies table
    """
    if not TMDB_API_TOKEN:
        logging.warning("TMDB_API_TOKEN not configured. Skipping movie population.")
        return False
    
    logging.info("Starting to fetch movies from TMDB API...")
    
    conn, error_info = get_db_connection()
    if not conn:
        logging.error(f"Could not connect to database: {error_info}")
        return False
    
    try:
        cur = conn.cursor()
        
        # Check if allMovies table already has data
        cur.execute("SELECT COUNT(*) FROM allMovies")
        count = cur.fetchone()[0]
        
        if count > 0:
            logging.info(f"allMovies table already has {count} movies. Skipping population.")
            cur.close()
            conn.close()
            return True
        
        total_movies_added = 0
        
        # Fetch first 10 pages from TMDB
        for page in range(1, 11):
            logging.info(f"Fetching page {page}/10 from TMDB...")
            
            try:
                response = requests.get(
                    'https://api.themoviedb.org/3/movie/popular',
                    params={'language': 'en-US', 'page': page},
                    headers={
                        'Authorization': f'Bearer {TMDB_API_TOKEN}',
                        'accept': 'application/json'
                    },
                    timeout=10
                )
                
                if response.status_code != 200:
                    logging.error(f"TMDB API returned status {response.status_code} for page {page}")
                    continue
                
                data = response.json()
                results = data.get('results', [])
                
                logging.info(f"Processing {len(results)} movies from page {page}...")
                
                for movie in results:
                    try:
                        # Extract movie data
                        title = movie.get('title') or movie.get('original_title', 'Unknown')
                        release_date = movie.get('release_date', '')
                        year = int(release_date.split('-')[0]) if release_date else 0
                        popularity = float(movie.get('popularity', 0.0))
                        
                        # Get first genre from genre_ids
                        genre_ids = movie.get('genre_ids', [])
                        genre = GENRE_MAP.get(genre_ids[0], 'Unknown') if genre_ids else 'Unknown'
                        
                        # Skip movies without valid year
                        if year == 0:
                            continue
                        
                        # Insert into allMovies table (ignore duplicates)
                        cur.execute(
                            """
                            INSERT INTO allMovies (name, genre, year, popularity)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (name, year) DO NOTHING
                            """,
                            (title, genre, year, popularity)
                        )
                        
                        total_movies_added += 1
                        
                    except Exception as e:
                        logging.warning(f"Error processing movie: {e}")
                        continue
                
                # Commit after each page
                conn.commit()
                logging.info(f"Page {page} processed successfully")
                
            except requests.exceptions.RequestException as e:
                logging.error(f"Error fetching page {page} from TMDB: {e}")
                continue
        
        cur.close()
        logging.info(f"✅ Successfully populated allMovies with {total_movies_added} movies from TMDB")
        return True
        
    except Exception as e:
        logging.error(f"Error populating movies from TMDB: {e}")
        return False
    finally:
        conn.close()

# Route to test the database connection
@app.route('/catalogue/test-db', methods=['GET'])
def test_db_connection():
    conn, error_info = get_db_connection()
    if conn:
        conn.close()
        return jsonify({"message": "Catalogue service: Database connected."}), 200
    # If connection failed, return debug info
    return jsonify(error_info), 500

# Get Movie list for a user
@app.route('/catalogue/movies', methods=['GET'])
def get_movies():
    import time
    start_time = time.time()
    logging.info(f"[TIMING] get_movies started")
    
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify(
            {
                "error": "User_id for the movie list is required"
            }
        ), 400

    # Get movies for the given user from the database
    logging.info(f"[TIMING] Before get_db_connection: {time.time() - start_time:.3f}s")
    conn, error_info = get_db_connection()
    logging.info(f"[TIMING] After get_db_connection: {time.time() - start_time:.3f}s")
    if conn:
        try:
            cur = conn.cursor()

            # Fetch movies associated with the user ID
            cur.execute(
                """
                SELECT name, genre, year
                FROM userMovies
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

            # Check if movie already exists in user's list
            cur.execute(
                """
                SELECT id FROM userMovies
                WHERE user_id = %s AND name = %s AND year = %s
                """,
                (user_id, name, year)
            )
            existing_movie = cur.fetchone()

            if existing_movie:
                cur.close()
                conn.close()
                return jsonify(
                    {
                        "error": f"Movie '{name}' ({year}) already exists in your list"
                    }
                ), 409  # 409 Conflict status code

            # Insert new movie for the user_id
            cur.execute(
                """
                INSERT INTO userMovies (user_id, name, genre, year)
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
                "SELECT id FROM userMovies "
                "WHERE name = %s AND year = %s AND user_id = %s",
                (name, year, user_id)
            )
            movie = cur.fetchone()

            if not movie:
                return jsonify({"error": "Movie not found"}), 404

            # Delete the movie
            cur.execute(
                "DELETE FROM userMovies "
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

# Get all movies from the master catalogue
@app.route('/catalogue/all-movies', methods=['GET'])
def get_all_movies():
    """
    Get all movies from the master catalogue (allMovies table)
    """
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # Fetch all movies from the catalogue
            cur.execute(
                """
                SELECT id, name, genre, year, popularity, avg_rating, review_count
                FROM allMovies
                ORDER BY name ASC
                """
            )

            movies = cur.fetchall()
            logging.debug(f"Found {len(movies)} movies in catalogue")

            if not movies:
                return jsonify(
                    {
                        "message": "No movies in catalogue yet",
                        "movies": []
                    }
                ), 200

            # Format the movie list
            movie_list = [
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
            return jsonify({"movies": movie_list}), 200
        except psycopg2.Error as e:
            return jsonify({"error": f"Error fetching catalogue: {str(e)}"}), 500
        finally:
            conn.close()

    return jsonify(error_info), 500

if __name__ == '__main__':
    logging.debug("Trying to initialize 'userMovies' and 'allMovies' tables in database...")
    while not initialize_table():
        pass
    logging.debug("'userMovies' and 'allMovies' tables created in database.")
    
    # Populate allMovies from TMDB API
    logging.info("Checking if allMovies table needs to be populated...")
    populate_movies_from_tmdb()
    
    app.run(debug=True, host='0.0.0.0', port=5001)
