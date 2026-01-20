# Movie Recommendation System Guide

## Overview

The Movie Catalogue now includes an intelligent recommendation system that suggests movies based on your genre preferences and TMDB popularity scores.

---

## How It Works

### 1. **Genre Selection**
- Choose from 18 different movie genres
- Click on genre chips to select/deselect
- Selected genres are highlighted in purple gradient
- You can select multiple genres at once

### 2. **Popularity Ranking**
- Movies are ranked by their TMDB popularity score
- Higher popularity = more popular/trending movie
- Only the **top 10 most popular** movies are shown
- Popularity score is displayed as a badge (⭐ XXX.X)

### 3. **Smart Matching**
- System finds movies matching **ANY** of your selected genres
- Results are sorted by popularity (most popular first)
- Each recommendation shows: name, genre, year, and popularity

---

## Using the Recommendation System

### Step-by-Step:

1. **Login** to your account
2. **Scroll down** to the "🎯 Get Recommendations" section
3. **Click on genres** you like (e.g., Action, Comedy, Horror)
   - Selected genres turn purple
   - Click again to deselect
4. **Click "Get Recommendations"** button
5. **Browse the results** - top 10 most popular movies
6. **Click "+ Add to My List"** to add any movie directly to your collection

---

## Available Genres

The system supports 18 genres:

**Adventure & Action:**
- Action
- Adventure
- War
- Western

**Comedy & Family:**
- Comedy
- Family
- Animation

**Drama & Emotion:**
- Drama
- Romance
- History

**Suspense & Thriller:**
- Thriller
- Crime
- Mystery

**Sci-Fi & Fantasy:**
- Science Fiction
- Fantasy

**Horror & Music:**
- Horror
- Music
- Documentary

---

## Understanding Popularity Scores

**Popularity Score** is a metric from TMDB that indicates how trending/popular a movie is:

- **300+** - Extremely popular, currently trending
- **100-300** - Very popular
- **50-100** - Popular
- **10-50** - Moderately popular
- **<10** - Less popular

The score is based on:
- Number of views on TMDB
- Number of votes
- Number of users who marked it as favorite
- Number of users who added it to their watchlist
- Release date (newer movies get a boost)

---

## Examples

### Example 1: Action Fan
**Selection:** Action, Thriller
**Result:** Top 10 action/thriller movies sorted by popularity
- The Dark Knight (⭐ 325.4)
- Inception (⭐ 298.7)
- John Wick (⭐ 267.3)
- ...

### Example 2: Family Movie Night
**Selection:** Family, Animation, Comedy
**Result:** Top 10 family-friendly movies
- Toy Story 4 (⭐ 412.8)
- Inside Out 2 (⭐ 387.2)
- Frozen (⭐ 299.1)
- ...

### Example 3: Horror Lover
**Selection:** Horror
**Result:** Top 10 horror movies by popularity
- A Quiet Place (⭐ 234.5)
- Get Out (⭐ 198.3)
- Hereditary (⭐ 176.9)
- ...

---

## Features

### ✅ **Multi-Genre Selection**
Select as many genres as you want for more diverse recommendations

### ✅ **One-Click Add**
Add recommended movies directly to your list without leaving the page

### ✅ **Real-Time Updates**
Get fresh recommendations every time you click "Get Recommendations"

### ✅ **Smart Filtering**
Only shows movies that exist in the catalogue (from TMDB popular movies)

### ✅ **Duplicate Prevention**
If you try to add a movie already in your list, you'll get a friendly error

### ✅ **No Authentication Required**
Recommendations work even if you're not logged in (but you need to login to add movies)

---

## API Reference

### Endpoint
```
POST /api/recommendations
```

### Request Body
```json
{
  "genres": ["Action", "Comedy", "Drama"],
  "limit": 10
}
```

**Parameters:**
- `genres` (required): Array of genre names
- `limit` (optional): Maximum number of recommendations (default: 20)

### Response
```json
{
  "recommendations": [
    {
      "id": 550,
      "name": "Fight Club",
      "genre": "Drama",
      "year": 1999,
      "popularity": 278.3709
    },
    {
      "id": 680,
      "name": "Pulp Fiction",
      "genre": "Crime",
      "year": 1994,
      "popularity": 245.6812
    }
  ]
}
```

### Error Responses

**400 Bad Request** - Missing or invalid genres:
```json
{
  "error": "Genres array is required"
}
```

**200 OK (Empty)** - No movies found:
```json
{
  "message": "No recommendations found for selected genres",
  "recommendations": []
}
```

---

## Technical Details

### Database Schema
```sql
CREATE TABLE allMovies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    genre VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    popularity FLOAT DEFAULT 0.0,  -- New field
    UNIQUE(name, year)
);
```

### SQL Query
```sql
SELECT id, name, genre, year, popularity
FROM allMovies
WHERE genre IN ('Action', 'Comedy', 'Drama')
ORDER BY popularity DESC
LIMIT 10;
```

### Architecture
```
Frontend (Genre Selection)
    ↓
API Service (/api/recommendations)
    ↓
Auth Service (/auth/recommendations)
    ↓
Catalogue Service (/catalogue/recommendations)
    ↓
PostgreSQL (allMovies table)
```

---

## Troubleshooting

### Issue: "No recommendations found"
**Solution:**
- Try selecting different genres
- Check if the catalogue has been populated (needs TMDB API token)
- Refresh the catalogue with the 🔄 button

### Issue: Can't select genres
**Solution:**
- Make sure you're logged in
- Check browser console for JavaScript errors
- Refresh the page

### Issue: Popularity scores seem wrong
**Solution:**
- Popularity scores come directly from TMDB
- They change over time based on movie trends
- To update, you need to repopulate the catalogue

---

## Future Enhancements

Potential improvements:
- [ ] User-based recommendations (based on movies in your list)
- [ ] Collaborative filtering (based on similar users)
- [ ] Recently added movies filter
- [ ] Year range filter (e.g., movies from 2020-2024)
- [ ] Rating-based recommendations
- [ ] "Similar to" feature (find movies similar to one you like)
- [ ] Save favorite genres in user profile
- [ ] Recommendation history

---

## Notes

- Recommendations are based on the movies currently in the catalogue (~200 popular movies)
- The catalogue is populated from TMDB "popular movies" endpoint
- Popularity scores are updated when the catalogue is repopulated
- The system requires a valid TMDB API token to work
- Recommendations are public (no authentication required to view)
- Adding movies to your list still requires authentication

---

Happy movie hunting! 🎬🍿
