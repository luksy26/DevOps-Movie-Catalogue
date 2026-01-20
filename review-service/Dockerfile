FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY review.py .

EXPOSE 8093

CMD ["python", "review.py"]
