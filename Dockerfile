# Use a lightweight, secure official Python base image
FROM python:3.11-slim

# Set the operational directory inside the container
WORKDIR /app

# Copy package dependency tracker first to optimize Docker layer caching
COPY requirements.txt .

# Install dependencies without saving local download caches
RUN pip install --no-cache-dir -r requirements.txt

# Copy the environment config, python scripts, and frontend assets
COPY .env .
COPY user_service.py .
COPY order_service.py .
COPY frontend/ frontend/

# Run Python with unbuffered outputs (-u) so container logs stream instantly
# Note: This is a default command and will be overridden by docker-compose for the User Service
CMD ["python", "-u", "order_service.py"]
