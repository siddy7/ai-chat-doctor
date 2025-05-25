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

# Copy Pipenv files and app code
COPY Pipfile Pipfile.lock ./
COPY . .

# Install pipenv and dependencies
RUN pip install pipenv && pipenv install --deploy --ignore-pipfile

# Streamlit port
EXPOSE 8501

CMD ["pipenv", "run", "streamlit", "run", "aichatdoctor.py", "--server.port=8501", "--server.enableCORS=false"]