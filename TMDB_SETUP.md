# TMDB API Setup Instructions

## Overview

The Movie Catalogue application now automatically populates the `allMovies` table with popular movies from The Movie Database (TMDB) API at startup.

## Getting Your TMDB API Token

1. **Create a TMDB Account**
   - Go to https://www.themoviedb.org/
   - Sign up for a free account

2. **Request API Access**
   - Go to your account settings: https://www.themoviedb.org/settings/api
   - Click on "Request an API Key"
   - Choose "Developer" option
   - Fill in the required information (you can use your project details)
   - Accept the terms of use

3. **Get Your Bearer Token**
   - Once approved, you'll see your API credentials
   - Copy the **"API Read Access Token (v4 auth)"** - this is your Bearer token
   - It looks like: `eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI...` (very long string)

## Configuring the Token

### Option 1: Update ConfigMap YAML (Before Deployment)

Edit `KubernetesConfigs/01-configMap.yaml`:

```yaml
data:
  TMDB_API_TOKEN: "YOUR_ACTUAL_TOKEN_HERE"
```

Then deploy:
```bash
./fullSetup.sh
```

### Option 2: Update ConfigMap in Running Cluster

If your cluster is already running:

```bash
# Edit the ConfigMap
kubectl edit configmap db-config-map

# Find the TMDB_API_TOKEN line and replace with your token
# Save and exit

# Restart the catalogue deployment to pick up the new token
kubectl rollout restart deployment catalogue-deployment
```

### Option 3: Using kubectl patch

```bash
kubectl patch configmap db-config-map -p '{"data":{"TMDB_API_TOKEN":"YOUR_ACTUAL_TOKEN_HERE"}}'
kubectl rollout restart deployment catalogue-deployment
```

## How It Works

1. When the catalogue service starts, it:
   - Creates the `userMovies` and `allMovies` tables
   - Checks if `allMovies` is empty
   - If empty, fetches the first 10 pages of popular movies from TMDB (~200 movies)
   - Extracts: title, genre (first genre), and release year
   - Inserts them into the `allMovies` table

2. The movies are then available in the "Browse Catalogue" tab in the frontend

3. If the table already has movies, it skips the population step (only runs once)

## Troubleshooting

### Check if token is configured:
```bash
kubectl get configmap db-config-map -o yaml | grep TMDB_API_TOKEN
```

### Check catalogue service logs:
```bash
kubectl logs -l app=catalogue --tail=100
```

Look for messages like:
- `✅ Successfully populated allMovies with XXX movies from TMDB`
- `TMDB_API_TOKEN not configured. Skipping movie population.`
- `allMovies table already has XXX movies. Skipping population.`

### Force repopulation:

If you want to repopulate the movies:

```bash
# Connect to the database
kubectl port-forward service/postgres-service 5432:5432

# In another terminal, connect with psql or DBeaver
# Database: movieApp, User: admin, Password: admin

# Clear the allMovies table
DELETE FROM allMovies;

# Restart the catalogue service
kubectl rollout restart deployment catalogue-deployment
```

## API Details

- **Endpoint**: `https://api.themoviedb.org/3/movie/popular`
- **Pages fetched**: 1-10
- **Movies per page**: ~20
- **Total movies**: ~200 popular movies
- **Language**: English (en-US)

## Genre Mapping

The application maps TMDB genre IDs to readable names:
- 28 → Action
- 35 → Comedy
- 18 → Drama
- 27 → Horror
- 878 → Science Fiction
- 53 → Thriller
- And more...

## Security Note

⚠️ **Important**: The TMDB API token is stored in a ConfigMap, which is not encrypted. For production use, consider using Kubernetes Secrets instead:

```bash
kubectl create secret generic tmdb-secret --from-literal=token=YOUR_TOKEN
```

Then update the deployment to use the secret instead of the ConfigMap.
