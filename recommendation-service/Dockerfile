FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY recommendation.py .

EXPOSE 8092

CMD ["python", "recommendation.py"]
