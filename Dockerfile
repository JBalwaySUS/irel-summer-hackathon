FROM python:3.9-slim

# Build argument to specify the service name (e.g., user_management)
ARG SERVICE_NAME

ENV PYTHONUNBUFFERED=1
# PORT is an environment variable that Cloud Run will set (default 8080).
# Uvicorn will listen on this port.
ENV PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Command to run the specified service using Uvicorn.
# services.${SERVICE_NAME}.main:app should point to your FastAPI app instance.
# Example: services.user_management.main:app
CMD exec uvicorn services.${SERVICE_NAME}.main:app --host 0.0.0.0 --port ${PORT}