#!/bin/bash

echo "Building Auth service Docker image..."
docker build -t auth-service:latest .
docker tag auth-service lucaslazaroiu/ccproject:auth-service
docker push lucaslazaroiu/ccproject:auth-service
echo "✅ Auth service image rebuilt and pushed"
