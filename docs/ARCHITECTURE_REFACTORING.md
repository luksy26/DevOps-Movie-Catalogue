# Architecture Refactoring - Microservices Separation

## Overview

The recommendation and review functionality has been refactored from the monolithic `catalogue-service` into separate microservices following best practices for microservices architecture.

---

## ✅ **What Changed**

### **Before: Monolithic Structure**
```
catalogue-service (port 5001)
├── Movie CRUD operations
├── TMDB population
├── Recommendations logic ❌
└── Reviews logic ❌
```

### **After: Microservices Structure**
```
catalogue-service (port 5001)
├── Movie CRUD operations
└── TMDB population

recommendation-service (port 8092) ✅
└── Recommendation logic

review-service (port 8093) ✅
└── Review & rating logic
```

---

## 🏗️ **New Services**

### **1. Recommendation Service**
- **Port**: 8092
- **Responsibilities**:
  - Get movie recommendations based on genres
  - Query allMovies table
  - Sort by popularity
  - Return top N results
- **Endpoints**:
  - `POST /recommendations` - Get recommendations
  - `GET /recommendations/test-db` - Test database connection
- **Database**: Reads from `allMovies` table

### **2. Review Service**
- **Port**: 8093
- **Responsibilities**:
  - Submit/update movie reviews
  - Calculate average ratings
  - Manage reviews table
  - Update allMovies ratings
- **Endpoints**:
  - `POST /reviews` - Submit review
  - `GET /reviews/<movie_id>` - Get movie reviews
  - `GET /reviews/test-db` - Test database connection
- **Database**: Reads/writes `reviews` table, updates `allMovies` table

### **3. Catalogue Service (Refactored)**
- **Port**: 5001
- **Responsibilities**:
  - Manage user movie lists (userMovies)
  - Manage master catalogue (allMovies)
  - Populate from TMDB API
  - CRUD operations on movies
- **Removed**: Recommendation and review endpoints
- **Database**: Manages `userMovies` and `allMovies` tables

---

## 📁 **New File Structure**

```
DevOps-Movie-Catalogue/
├── recommendation-service/
│   ├── recommendation.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── rebuildImage.sh
│
├── review-service/
│   ├── review.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── rebuildImage.sh
│
├── catalogue-service/
│   ├── catalogue.py (refactored - slimmed down)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── rebuildImage.sh
│
└── KubernetesConfigs/
    ├── 16-recommendation-deployment.yaml (new)
    ├── 17-recommendation-ClusterIP.yaml (new)
    ├── 18-review-deployment.yaml (new)
    └── 19-review-ClusterIP.yaml (new)
```

---

## 🔄 **Request Flow**

### **Before (Monolithic)**:
```
Frontend → API → Auth → Catalogue (handles everything)
```

### **After (Microservices)**:
```
Frontend → API → Auth → Catalogue (for movies)
                     ↓
                     → Recommendation (for recommendations)
                     ↓
                     → Review (for reviews/ratings)
```

---

## 🔌 **Service Communication**

### **Auth Service Environment Variables**:
```yaml
CATALOGUE_SERVICE_URL: "http://catalogue-service:8091"
RECOMMENDATION_SERVICE_URL: "http://recommendation-service:8092"
REVIEW_SERVICE_URL: "http://review-service:8093"
```

### **Kubernetes Services**:
- `catalogue-service` (ClusterIP) → port 8091
- `recommendation-service` (ClusterIP) → port 8092
- `review-service` (ClusterIP) → port 8093

All services communicate internally via Kubernetes DNS.

---

## 📊 **Benefits of This Refactoring**

### **1. Separation of Concerns**
- Each service has a single, well-defined responsibility
- Easier to understand and maintain
- Clear boundaries between components

### **2. Independent Scaling**
- Scale recommendation service independently (high read load)
- Scale review service independently (write-heavy operations)
- Scale catalogue service based on its own needs

### **3. Independent Deployment**
- Deploy recommendation updates without touching reviews
- Deploy review updates without affecting catalogue
- Reduced risk of breaking changes

### **4. Technology Flexibility**
- Each service can use different tech stacks if needed
- Can optimize each service differently
- Easier to adopt new technologies per service

### **5. Fault Isolation**
- If recommendation service fails, reviews still work
- If review service fails, catalogue browsing still works
- Better resilience and fault tolerance

### **6. Team Organization**
- Different teams can own different services
- Clear ownership boundaries
- Parallel development possible

---

## 🚀 **Deployment**

### **Build All Services**:
```bash
cd /Users/llazaroiu/DevOps-Movie-Catalogue
./rebuildAllImages.sh
```

This now builds **5 services**:
1. API Service
2. Auth Service
3. Catalogue Service
4. Recommendation Service ✅ NEW
5. Review Service ✅ NEW

### **Deploy to Kubernetes**:
```bash
cd terraform-infra
terraform apply
```

Or update running cluster:
```bash
./updateServiceIPs.sh
```

### **Restart Services**:
```bash
./restartDeployments.sh
```

Now restarts all 5 services.

---

## 📝 **Updated Scripts**

### **rebuildAllImages.sh**:
- Now builds 5 images instead of 3
- Added recommendation-service build step
- Added review-service build step

### **restartDeployments.sh**:
- Restarts all 5 deployments
- Includes recommendation-deployment
- Includes review-deployment

### **fullSetup.sh**:
- Complete setup including new services
- Builds all 5 images
- Deploys all services

### **updateServiceIPs.sh**:
- Gets ClusterIPs for all services
- Updates all deployment manifests
- Includes recommendation and review services

### **forceFixDeployments.sh**:
- Scales down/up all 5 services
- Gracefully handles missing services

---

## 🧪 **Testing the Refactoring**

### **1. Test Each Service Independently**:

```bash
# Test recommendation service
kubectl port-forward service/recommendation-service 8092:8092
curl -X POST http://localhost:8092/recommendations \
  -H "Content-Type: application/json" \
  -d '{"genres": ["Action", "Comedy"], "limit": 5}'

# Test review service
kubectl port-forward service/review-service 8093:8093
curl http://localhost:8093/reviews/123
```

### **2. Test End-to-End**:
- Login to frontend
- Browse catalogue (should work)
- Get recommendations (should work)
- Submit a review (should work)
- See updated ratings (should work)

### **3. Check Service Health**:
```bash
kubectl get pods
kubectl get services
kubectl logs -l app=recommendation
kubectl logs -l app=review
```

---

## 📈 **Monitoring Considerations**

With microservices, consider:
- **Distributed Tracing**: Track requests across services
- **Centralized Logging**: Aggregate logs from all services
- **Service Mesh**: Consider Istio or Linkerd for advanced features
- **Health Checks**: Each service should have health endpoints

---

## 🔮 **Future Enhancements**

### **Possible Next Steps**:
1. **Add API Gateway** (Kong, Traefik) instead of custom API service
2. **Service Mesh** (Istio) for traffic management
3. **Message Queue** (RabbitMQ, Kafka) for async communication
4. **Caching Layer** (Redis) for frequently accessed data
5. **Separate Databases** per service (true microservices pattern)

---

## 🎯 **Architecture Diagram**

```
┌─────────┐
│ Frontend│
└────┬────┘
     │
┌────▼─────┐
│   API    │
│ Service  │
└────┬─────┘
     │
┌────▼─────┐
│   Auth   │
│ Service  │
└────┬─────┘
     │
     ├─────────────────┬────────────────┬────────────────┐
     │                 │                │                │
┌────▼────┐      ┌─────▼─────┐  ┌──────▼──────┐  ┌─────▼──────┐
│Catalogue│      │Recommenda-│  │   Review    │  │  Postgres  │
│ Service │      │   tion    │  │   Service   │  │  Database  │
│(port 5001)     │  Service  │  │ (port 8093) │  │            │
└──────────┘     │(port 8092)│  └─────────────┘  └────────────┘
                 └───────────┘
```

---

## ✅ **Migration Complete!**

The refactoring is complete and the system now follows proper microservices architecture principles!

**Benefits**:
- ✅ Better separation of concerns
- ✅ Independent scaling
- ✅ Fault isolation
- ✅ Independent deployment
- ✅ Cleaner codebase
- ✅ Professional architecture

---

**Note**: All existing functionality remains the same from the user's perspective. This is a behind-the-scenes architectural improvement!
