#!/bin/bash

echo "Building Recommendation service Docker image..."
docker build -t recommendation-service:latest .
docker tag recommendation-service lucaslazaroiu/ccproject:recommendation-service
docker push lucaslazaroiu/ccproject:recommendation-service
echo "✅ Recommendation service image rebuilt and pushed"
