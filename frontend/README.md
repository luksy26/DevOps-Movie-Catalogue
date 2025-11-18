# Movie Catalogue Frontend

A beautiful, modern single-page application for managing your movie catalogue.

## Features

✨ **User Authentication**
- User registration
- Login with JWT tokens
- Session management (token stored in memory)

🎬 **Movie Management**
- View all your movies
- Add new movies (name, genre, year)
- Delete movies
- Beautiful card-based UI

📊 **Database Status**
- Real-time database connection indicator
- Visual feedback with animated status dot

## How to Run

### Prerequisites
- Your Kubernetes cluster must be running
- API service must be accessible at `http://localhost:30000`

### Start the Frontend

```bash
cd frontend
./serve.sh
```

Then open your browser to: **http://localhost:8000**

## Usage

### 1. Register a New Account
- Click "Don't have an account? Register"
- Enter a username and password
- Click "Register"
- You'll see a success message

### 2. Login
- Enter your username and password
- Click "Login"
- You'll be taken to the movies dashboard

### 3. Add Movies
- Fill in the movie name, genre, and year
- Click "Add Movie"
- The movie will appear in your list

### 4. Delete Movies
- Click the "Delete" button on any movie card
- Confirm the deletion
- The movie will be removed from your list

### 5. Check Database Status
- Look at the top of the page for the database status indicator
- Green dot = Connected
- Gray dot = Disconnected

## API Endpoints Used

- `GET /api/testauth` - Check database connection
- `POST /api/register` - Register new user
- `POST /api/login` - Login and get JWT token
- `GET /api/movies` - Get user's movies
- `POST /api/movies` - Add a new movie
- `DELETE /api/movies` - Delete a movie

## Security Notes

- JWT tokens are stored in memory (not localStorage/cookies)
- Tokens expire after 1 hour
- All movie operations require authentication
- Automatic logout on token expiration

## Design

- Modern gradient design
- Responsive layout
- Smooth animations
- Clean, intuitive interface
- Error handling with user-friendly messages

## Troubleshooting

**Can't connect to API:**
- Make sure your Kubernetes cluster is running
- Verify the API service is exposed on port 30000
- Check: `kubectl get svc -n default`

**Database shows disconnected:**
- Check postgres pod is running: `kubectl get pods -n default`
- Verify auth service is running

**Token expired:**
- Simply login again to get a new token
- Tokens are valid for 1 hour

## Tech Stack

- Pure HTML5, CSS3, JavaScript
- No frameworks needed
- Fetch API for HTTP requests
- Modern ES6+ JavaScript

