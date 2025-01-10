docker build -t api-service:latest .
docker tag api-service lucaslazaroiu/ccproject:api-service
docker push lucaslazaroiu/ccproject:api-service
