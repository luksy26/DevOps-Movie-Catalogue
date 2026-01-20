#!/bin/bash

echo "Building Notification service Docker image..."
docker build -t notification-service:latest .
docker tag notification-service:latest lucaslazaroiu/ccproject:notification-service
docker push lucaslazaroiu/ccproject:notification-service
echo "✅ Notification service image rebuilt and pushed"
