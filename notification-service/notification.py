from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2 import OperationalError
import os
import logging
import requests
import random
import time
import threading
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
TMDB_UPCOMING_URL = "https://api.themoviedb.org/3/movie/upcoming"

# SMTP configuration for Mailpit
SMTP_HOST = os.environ.get("SMTP_HOST", "mailpit")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 1025))
SMTP_FROM = os.environ.get("SMTP_FROM", "notifications@movieapp.local")
EMAIL_ENABLED = os.environ.get("EMAIL_ENABLED", "true").lower() == "true"

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

# Function to initialize tables
def initialize_tables():
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()

            # Create `user_sessions` table to track active users
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INT NOT NULL UNIQUE,
                    user_email VARCHAR(255),
                    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_notification_time TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
                """
            )

            # Create `notifications` table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INT NOT NULL,
                    movie_id INT NOT NULL,
                    movie_title VARCHAR(255) NOT NULL,
                    movie_overview TEXT,
                    movie_poster_path VARCHAR(255),
                    movie_release_date VARCHAR(20),
                    movie_rating FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE
                )
                """
            )

            conn.commit()  # Save changes
            cur.close()
            logging.info("✅ Notification tables initialized successfully")
            return True
        except Exception as e:
            logging.error(f"❌ Error initializing notification tables: {e}")
            return False
        finally:
            conn.close()
    else:
        logging.error(f"❌ Database connection failed: {error_info}")
    return False

# Send email notification
def send_email_notification(to_email, movie_title, movie_overview, movie_rating, movie_release_date, movie_poster_path):
    """Send email notification for a new movie recommendation"""
    if not EMAIL_ENABLED:
        logging.debug("📧 Email notifications disabled")
        return False
    
    if not to_email:
        logging.warning("⚠️  No email address provided, skipping email")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_FROM
        msg['To'] = to_email
        msg['Subject'] = f"🎬 New Movie Recommendation: {movie_title}"
        
        # Create HTML body
        poster_url = f"https://image.tmdb.org/t/p/w500{movie_poster_path}" if movie_poster_path else ""
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .movie-title {{ font-size: 24px; font-weight: bold; margin-bottom: 15px; color: #667eea; }}
                .movie-info {{ margin: 15px 0; }}
                .rating {{ color: #ffa500; font-weight: bold; }}
                .poster {{ max-width: 300px; border-radius: 10px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #999; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎬 New Movie Recommendation!</h1>
                </div>
                <div class="content">
                    <div class="movie-title">{movie_title}</div>
                    <div class="movie-info">
                        <p><span class="rating">⭐ {movie_rating:.1f}/10</span> | 📅 {movie_release_date}</p>
                    </div>
                    {"<img src='" + poster_url + "' class='poster' alt='Movie Poster'>" if poster_url else ""}
                    <p>{movie_overview}</p>
                    <div class="footer">
                        <p>This is an automated notification from Movie Catalogue App</p>
                        <p>Login to view more details and add this movie to your watchlist!</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML body
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.send_message(msg)
            logging.info(f"📧 Email sent to {to_email}: {movie_title}")
            return True
            
    except Exception as e:
        logging.error(f"❌ Failed to send email to {to_email}: {e}")
        return False

# Fetch upcoming movies from TMDB
def fetch_upcoming_movies():
    """Fetch upcoming movies from TMDB API"""
    if not TMDB_API_TOKEN:
        logging.error("TMDB_API_TOKEN not configured")
        return []
    
    try:
        headers = {
            "Authorization": f"Bearer {TMDB_API_TOKEN}",
            "accept": "application/json"
        }
        params = {
            "language": "en-US",
            "page": random.randint(1, 5)  # Random page from first 5 pages
        }
        
        response = requests.get(TMDB_UPCOMING_URL, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
        else:
            logging.error(f"Failed to fetch upcoming movies: {response.status_code}")
            return []
    except Exception as e:
        logging.error(f"Error fetching upcoming movies: {e}")
        return []

# Background task to send notifications
def notification_background_task():
    """Background task that periodically sends movie recommendations to active users"""
    logging.info("🔔 Notification background task started")
    
    while True:
        try:
            # Random sleep between 20-30 seconds
            sleep_time = random.randint(20, 30)
            logging.debug(f"💤 Sleeping for {sleep_time} seconds before next notification check...")
            time.sleep(sleep_time)
            
            conn, error_info = get_db_connection()
            if not conn:
                logging.error(f"Failed to connect to database: {error_info}")
                continue
            
            try:
                cur = conn.cursor()
                
                # Find active users who haven't received a notification recently
                # (or never received one, or it's been more than 20 seconds)
                cur.execute(
                    """
                    SELECT user_id, user_email, last_notification_time
                    FROM user_sessions
                    WHERE is_active = TRUE
                    AND (
                        last_notification_time IS NULL
                        OR last_notification_time < NOW() - INTERVAL '20 seconds'
                    )
                    """
                )
                
                active_users = cur.fetchall()
                
                if not active_users:
                    logging.debug("No active users eligible for notifications")
                    cur.close()
                    conn.close()
                    continue
                
                logging.info(f"📢 Found {len(active_users)} users eligible for notifications")
                
                # Fetch upcoming movies
                upcoming_movies = fetch_upcoming_movies()
                
                if not upcoming_movies:
                    logging.warning("No upcoming movies available")
                    cur.close()
                    conn.close()
                    continue
                
                # Send notification to each eligible user
                for user_id, user_email, last_notif_time in active_users:
                    # Pick a random movie
                    movie = random.choice(upcoming_movies)
                    
                    movie_title = movie.get("title", "Unknown")
                    movie_overview = movie.get("overview", "")
                    movie_poster_path = movie.get("poster_path", "")
                    movie_release_date = movie.get("release_date", "")
                    movie_rating = movie.get("vote_average", 0.0)
                    
                    # Insert notification
                    cur.execute(
                        """
                        INSERT INTO notifications 
                        (user_id, movie_id, movie_title, movie_overview, 
                         movie_poster_path, movie_release_date, movie_rating)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            user_id,
                            movie.get("id"),
                            movie_title,
                            movie_overview,
                            movie_poster_path,
                            movie_release_date,
                            movie_rating
                        )
                    )
                    
                    # Send email notification
                    if user_email:
                        send_email_notification(
                            user_email,
                            movie_title,
                            movie_overview,
                            movie_rating,
                            movie_release_date,
                            movie_poster_path
                        )
                    else:
                        logging.debug(f"⚠️  User {user_id} has no email address, skipping email notification")
                    
                    # Update last notification time
                    cur.execute(
                        """
                        UPDATE user_sessions
                        SET last_notification_time = NOW()
                        WHERE user_id = %s
                        """,
                        (user_id,)
                    )
                    
                    logging.info(f"✅ Sent notification to user {user_id}: {movie.get('title')}")
                
                conn.commit()
                cur.close()
                
            finally:
                conn.close()
                
        except Exception as e:
            logging.error(f"Error in notification background task: {e}")
            time.sleep(10)  # Wait a bit before retrying

# Route to test the database connection
@app.route('/notifications/test-db', methods=['GET'])
def test_db_connection():
    conn, error_info = get_db_connection()
    if conn:
        conn.close()
        return jsonify({"message": "Notification service: Database connected."}), 200
    # If connection failed, return debug info
    return jsonify(error_info), 500

# Route to register/update user session (called on login)
@app.route('/notifications/session', methods=['POST'])
def update_session():
    """Register or update user session"""
    data = request.get_json()
    user_id = data.get('user_id')
    user_email = data.get('user_email', None)  # Optional email
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Upsert user session with email
            cur.execute(
                """
                INSERT INTO user_sessions (user_id, user_email, login_time, is_active)
                VALUES (%s, %s, NOW(), TRUE)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    user_email = COALESCE(EXCLUDED.user_email, user_sessions.user_email),
                    login_time = NOW(),
                    is_active = TRUE,
                    last_notification_time = NULL
                """,
                (user_id, user_email)
            )
            
            conn.commit()
            cur.close()
            
            if user_email:
                logging.info(f"✅ User session registered: {user_id} ({user_email})")
            else:
                logging.info(f"✅ User session registered: {user_id} (no email)")
            return jsonify({"message": "Session registered successfully"}), 200
            
        except psycopg2.Error as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            conn.close()
    
    return jsonify(error_info), 500

# Route to mark session as inactive (called on logout)
@app.route('/notifications/session/<int:user_id>', methods=['DELETE'])
def end_session(user_id):
    """Mark user session as inactive"""
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            cur.execute(
                """
                UPDATE user_sessions
                SET is_active = FALSE
                WHERE user_id = %s
                """,
                (user_id,)
            )
            
            conn.commit()
            cur.close()
            
            logging.info(f"✅ User session ended: {user_id}")
            return jsonify({"message": "Session ended successfully"}), 200
            
        except psycopg2.Error as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            conn.close()
    
    return jsonify(error_info), 500

# Route to get user notifications
@app.route('/notifications/<int:user_id>', methods=['GET'])
def get_notifications(user_id):
    """Get all notifications for a user"""
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            cur.execute(
                """
                SELECT id, movie_id, movie_title, movie_overview, 
                       movie_poster_path, movie_release_date, movie_rating,
                       created_at, is_read
                FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 50
                """,
                (user_id,)
            )
            
            notifications = cur.fetchall()
            
            notification_list = [
                {
                    "id": notif[0],
                    "movie_id": notif[1],
                    "movie_title": notif[2],
                    "movie_overview": notif[3],
                    "movie_poster_path": notif[4],
                    "movie_release_date": notif[5],
                    "movie_rating": notif[6],
                    "created_at": notif[7].isoformat() if notif[7] else None,
                    "is_read": notif[8]
                }
                for notif in notifications
            ]
            
            cur.close()
            return jsonify({"notifications": notification_list}), 200
            
        except psycopg2.Error as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            conn.close()
    
    return jsonify(error_info), 500

# Route to mark notification as read
@app.route('/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            cur.execute(
                """
                UPDATE notifications
                SET is_read = TRUE
                WHERE id = %s
                """,
                (notification_id,)
            )
            
            conn.commit()
            cur.close()
            
            return jsonify({"message": "Notification marked as read"}), 200
            
        except psycopg2.Error as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            conn.close()
    
    return jsonify(error_info), 500

# Route to get unread notification count
@app.route('/notifications/<int:user_id>/unread-count', methods=['GET'])
def get_unread_count(user_id):
    """Get count of unread notifications"""
    conn, error_info = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            cur.execute(
                """
                SELECT COUNT(*)
                FROM notifications
                WHERE user_id = %s AND is_read = FALSE
                """,
                (user_id,)
            )
            
            count = cur.fetchone()[0]
            cur.close()
            
            return jsonify({"unread_count": count}), 200
            
        except psycopg2.Error as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            conn.close()
    
    return jsonify(error_info), 500

if __name__ == '__main__':
    # Initialize database tables
    logging.info("🔄 Trying to initialize notification tables...")
    max_retries = 30
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        if initialize_tables():
            logging.info("✅ Notification tables created in database.")
            break
        logging.warning(f"⚠️  Database not ready, retrying... (attempt {attempt + 1}/{max_retries})")
        time.sleep(retry_delay)
    else:
        logging.error("❌ Failed to initialize database after maximum retries. Starting app anyway...")
    
    # Start background notification task
    notification_thread = threading.Thread(target=notification_background_task, daemon=True)
    notification_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=8094)
