# Changelog

## Recent Updates

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
