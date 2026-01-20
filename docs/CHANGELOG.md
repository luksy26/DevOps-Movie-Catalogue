# Changelog

## Recent Updates

### Movie Review & Rating System

**Added**: Comprehensive review and rating system allowing users to rate movies (1-5 stars) and write reviews.

#### Features:

**Rating System**:
- Users can rate any movie from 1 to 5 stars
- Ratings are averaged across all users
- Each movie displays its average rating and review count
- Star rating displayed with ★ symbols (visual feedback)

**Review Submission**:
- Users can write text reviews (optional)
- One review per user per movie (updates if user reviews again)
- Requires authentication to submit reviews
- Beautiful modal interface for rating/reviewing

**Display**:
- Ratings shown in catalogue browse view
- Ratings shown in recommendations
- "No ratings yet" for unrated movies
- Review count displayed next to rating
- ⭐ Rate button on each movie

**Data Management**:
- Automatic average rating calculation
- Review count tracking
- Prevents duplicate reviews (one per user per movie)
- Updates allowed (user can change their rating/review)

#### Technical Implementation:

**Database Changes**:
- Added `reviews` table:
  - `movie_id` (foreign key to allMovies)
  - `user_id` (identifies reviewer)
  - `rating` (1-5, with CHECK constraint)
  - `review_text` (optional TEXT field)
  - `created_at` (timestamp)
  - UNIQUE constraint on (movie_id, user_id)
- Added to `allMovies` table:
  - `avg_rating` (FLOAT, default 0.0)
  - `review_count` (INT, default 0)

**Backend (Catalogue Service)**:
- `POST /catalogue/reviews` - Submit/update review
  - Validates rating (1-5 range)
  - UPSERT operation (insert or update)
  - Automatically recalculates average rating
  - Returns new average and review count
- `GET /catalogue/reviews/<movie_id>` - Get all reviews for a movie
  - Returns movie info with average rating
  - Returns list of all reviews with user IDs
- Updated existing endpoints to include ratings in responses

**Middleware (Auth & API Services)**:
- `POST /auth/reviews` - Requires JWT token, extracts user_id
- `GET /auth/reviews/<movie_id>` - Public, no auth required
- `POST /api/reviews` - Forwards with auth token
- `GET /api/reviews/<movie_id>` - Public endpoint

**Frontend**:
- **Star Rating Display**: Helper function `generateStars(rating, count)`
- **Review Modal**: Beautiful overlay modal for rating/reviewing
  - Interactive star rating (click to select)
  - Hover effects on stars
  - Optional text review area
  - Real-time validation
  - Success/error feedback
- **Updated Movie Cards**: Show ratings and "⭐ Rate" button
- **Ratings in Catalogue**: Browse tab shows ratings
- **Ratings in Recommendations**: All recommendations show ratings

#### User Flow:

1. **Browse movies** in catalogue or recommendations
2. **See ratings** - average stars and review count
3. **Click "⭐ Rate"** button on any movie
4. **Modal opens** showing movie details
5. **Select rating** (1-5 stars with visual feedback)
6. **Write review** (optional text)
7. **Submit** - new average calculated and displayed
8. **Reload** - updated ratings show everywhere

#### API Examples:

**Submit Review:**
```json
POST /api/reviews
Headers: { "Authorization": "token" }
Body: {
  "movie_id": 123,
  "rating": 4,
  "review_text": "Great movie!"
}

Response: {
  "message": "Review submitted successfully",
  "new_avg_rating": 4.2,
  "total_reviews": 15
}
```

**Get Reviews:**
```json
GET /api/reviews/123

Response: {
  "movie": {
    "id": 123,
    "name": "The Matrix",
    "avg_rating": 4.2,
    "review_count": 15
  },
  "reviews": [
    {
      "user_id": 456,
      "rating": 5,
      "review_text": "Amazing!",
      "created_at": "2026-01-20T..."
    }
  ]
}
```

---

### Movie Recommendation System

**Added**: Intelligent movie recommendation system based on genre preferences and popularity.

#### Features:

**Genre-Based Recommendations**:
- Users can select from 18 different genres (Action, Comedy, Drama, Horror, etc.)
- Multi-genre selection supported (select multiple genres at once)
- Visual chip-based genre selection interface
- Selected genres are highlighted with gradient background

**Popularity-Based Ranking**:
- Recommendations are sorted by TMDB popularity score
- Shows top 10 most popular movies for selected genres
- Popularity score displayed as a badge with each recommendation
- Real popularity data from TMDB API

**User Experience**:
- Clean, modern UI with genre chips
- Add recommended movies directly to your list with one click
- Real-time recommendation updates
- Empty state handling for no results
- Loading states and error handling

#### Technical Implementation:

**Database Changes**:
- Added `popularity` column to `allMovies` table (FLOAT type)
- Stores TMDB popularity score for each movie
- Updated TMDB fetching to include popularity data

**Backend (Catalogue Service)**:
- New endpoint: `POST /catalogue/recommendations`
- Accepts: `{ "genres": ["Action", "Comedy"], "limit": 10 }`
- Returns: Movies matching ANY selected genre, sorted by popularity DESC
- Parameterized SQL queries for security

**Middleware (Auth & API Services)**:
- Added `/auth/recommendations` endpoint (forwards to catalogue)
- Added `/api/recommendations` endpoint (forwards to auth)
- Public endpoint - no authentication required

**Frontend**:
- New "Get Recommendations" section after movie list
- 18 genre chips for selection (matching backend GENRE_MAP)
- Toggle selection on/off with visual feedback
- Recommendations displayed in cards with popularity badges
- Direct "Add to My List" button for each recommendation

#### Usage:

1. Login to the application
2. Scroll down to "🎯 Get Recommendations" section
3. Click on genres you like (e.g., Action, Comedy, Thriller)
4. Click "Get Recommendations" button
5. See top 10 most popular movies from those genres
6. Add movies to your list with one click

#### API Details:

**Request:**
```json
POST /api/recommendations
{
  "genres": ["Action", "Comedy", "Drama"],
  "limit": 10
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "id": 123,
      "name": "The Matrix",
      "genre": "Action",
      "year": 1999,
      "popularity": 278.37
    }
  ]
}
```

---

### Performance Optimization - Catalogue Loading

**Fixed**: Catalogue now loads only once instead of on every tab click.

#### Changes:

**Frontend**:
- Added `catalogueLoaded` flag to track if catalogue has been fetched
- Catalogue API call now only happens:
  - On first click to "Browse Catalogue" tab
  - When user manually clicks refresh button (🔄)
  - After logout/login (state resets)
- Added manual refresh button (🔄) in catalogue header for users who want to reload
- Improved performance by eliminating redundant API calls

**Benefits**:
- ✅ Faster tab switching (no loading delay)
- ✅ Reduced server load
- ✅ Better user experience
- ✅ Manual refresh option still available

---

### Duplicate Movie Prevention

**Added**: Logic to prevent users from adding the same movie twice to their list.

#### Changes:

**Catalogue Service**:
- Added duplicate check before insertion in `add_movie()` endpoint
- Queries `userMovies` table to check if movie (by name and year) already exists for the user
- Returns `409 Conflict` status with descriptive error message if duplicate found

**Auth Service**:
- Added handling for `409` status code from catalogue service
- Passes through the duplicate error message to API layer

**API Service**:
- Added handling for `409` status code from auth service
- Returns clear error message to frontend

**Frontend**:
- Added special handling for `409` status code
- Shows user-friendly error message: "This movie is already in your list"
- Auto-dismisses duplicate error after 3 seconds
- Works for both manual entry and catalogue browsing

---

### Browse Catalogue Feature + TMDB Integration

#### Database Changes
- **Renamed** `movies` table → `userMovies` (stores user-specific movie lists)
- **Created** `allMovies` table (master catalogue with UNIQUE constraint on name+year)

#### Backend Changes

**Catalogue Service** (`catalogue-service/catalogue.py`):
- Added TMDB API integration with `populate_movies_from_tmdb()` function
- Fetches first 10 pages (~200 movies) from TMDB popular movies endpoint
- Maps TMDB genre IDs to readable genre names
- Auto-populates `allMovies` table at startup (only if empty)
- New endpoint: `GET /catalogue/all-movies` - returns all movies from master catalogue
- Updated all queries to use `userMovies` instead of `movies`
- Added `requests` library to requirements.txt

**Auth Service** (`auth-service/auth.py`):
- New endpoint: `GET /auth/all-movies` - forwards to catalogue service (public, no auth)

**API Service** (`api-service/api.py`):
- New endpoint: `GET /api/all-movies` - public endpoint for frontend

#### Frontend Changes (`frontend/index.html`):
- Added tabbed interface for adding movies:
  - **Browse Catalogue** tab: Browse and add movies from master catalogue
  - **Manual Entry** tab: Original manual movie entry form
- New CSS styles for tabs and catalogue items
- New JavaScript functions:
  - `showAddTab(tab)` - switch between tabs
  - `loadCatalogue()` - fetch and display all movies
  - `addMovieFromCatalogue(movie)` - add movie from catalogue to user's list
- Auto-loads catalogue when user logs in

#### Configuration Changes

**ConfigMap** (`KubernetesConfigs/01-configMap.yaml`):
- Added `TMDB_API_TOKEN` configuration key

**Catalogue Deployment** (`KubernetesConfigs/10-catalogue-deployment.yaml`):
- Added `TMDB_API_TOKEN` environment variable from ConfigMap

#### DevOps Scripts

**New Scripts**:
- `api-service/rebuildImage.sh` - rebuild API service Docker image
- `auth-service/rebuildImage.sh` - rebuild Auth service Docker image
- `catalogue-service/rebuildImage.sh` - rebuild Catalogue service Docker image
- `rebuildAllImages.sh` - rebuild all three service images
- `restartDeployments.sh` - restart all Kubernetes deployments

**Updated Scripts**:
- `fullSetup.sh` - now includes Docker image rebuild step (Step 2)

#### Documentation

**New Files**:
- `TMDB_SETUP.md` - detailed instructions for getting and configuring TMDB API token
- `CHANGELOG.md` - this file

**Updated Files**:
- `README.md` - added TMDB setup instructions and updated feature list

---

## How to Deploy These Changes

### Option 1: Full Setup (Recommended)
```bash
# 1. Get your TMDB API token from https://www.themoviedb.org/settings/api
# 2. Edit KubernetesConfigs/01-configMap.yaml and add your token
# 3. Run full setup
./fullSetup.sh
```

### Option 2: Update Running Cluster
```bash
# 1. Rebuild images
./rebuildAllImages.sh

# 2. Update ConfigMap with your TMDB token
kubectl patch configmap db-config-map -p '{"data":{"TMDB_API_TOKEN":"YOUR_TOKEN"}}'

# 3. Restart deployments
./restartDeployments.sh
```

---

## Testing the New Features

1. **Browse Catalogue**:
   - Login to the application
   - Click on "Browse Catalogue" tab
   - You should see ~200 popular movies (if TMDB token is configured)
   - Click "+ Add to My List" on any movie

2. **Manual Entry** (still works):
   - Click on "Manual Entry" tab
   - Enter movie details manually
   - Click "Add Movie"

3. **View Your Movies**:
   - Scroll down to "Your Movies" section
   - See movies added from both sources

---

## Technical Details

### API Flow
```
Frontend → API Service → Auth Service → Catalogue Service → PostgreSQL
```

### TMDB Integration
- **API**: The Movie Database (TMDB) v3
- **Endpoint**: `https://api.themoviedb.org/3/movie/popular`
- **Pages**: 1-10 (configurable)
- **Authentication**: Bearer token
- **Rate Limiting**: Respects TMDB API limits
- **Error Handling**: Graceful fallback if API unavailable

### Database Schema
```sql
-- User-specific movies
CREATE TABLE userMovies (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    genre VARCHAR(100) NOT NULL,
    year INT NOT NULL
);

-- Master catalogue
CREATE TABLE allMovies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    genre VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    UNIQUE(name, year)
);
```

---

## Future Enhancements

Potential improvements:
- [ ] Search/filter functionality in catalogue browser
- [ ] Pagination for large catalogues
- [ ] Admin panel to manage catalogue
- [ ] Sync with TMDB on schedule (cron job)
- [ ] Movie details (poster, description, ratings)
- [ ] Multiple genres per movie
- [ ] User ratings and reviews
