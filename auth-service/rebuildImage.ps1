docker build -t auth-service:latest .
docker tag auth-service lucaslazaroiu/ccproject:auth-service
docker push lucaslazaroiu/ccproject:auth-service
