# Dockerfile
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app
COPY . .

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Streamlit port
EXPOSE 8501

CMD ["streamlit", "run", "aichatdoctor.py", "--server.port=8501", "--server.address=0.0.0.0"]