#!/bin/bash

echo "Building Catalogue service Docker image..."
docker build -t catalogue-service:latest .
docker tag catalogue-service lucaslazaroiu/ccproject:catalogue-service
docker push lucaslazaroiu/ccproject:catalogue-service
echo "✅ Catalogue service image rebuilt and pushed"
