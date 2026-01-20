#!/bin/bash

echo "Building Review service Docker image..."
docker build -t review-service:latest .
docker tag review-service lucaslazaroiu/ccproject:review-service
docker push lucaslazaroiu/ccproject:review-service
echo "✅ Review service image rebuilt and pushed"
