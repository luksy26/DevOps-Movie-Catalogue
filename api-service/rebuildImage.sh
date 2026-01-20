#!/bin/bash

echo "Building API service Docker image..."
docker build -t api-service:latest .
docker tag api-service lucaslazaroiu/ccproject:api-service
docker push lucaslazaroiu/ccproject:api-service
echo "✅ API service image rebuilt and pushed"
