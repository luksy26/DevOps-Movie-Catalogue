# Changelog

## Recent Updates

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
