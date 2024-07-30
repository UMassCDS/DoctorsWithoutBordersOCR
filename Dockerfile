# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Setting work directory
WORKDIR /app

# Getting git to clone and system dependencies for DocTR
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 libhdf5-dev pkg-config \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copying app files into container
COPY . .

# Install pip requirements
RUN pip install --no-cache-dir .[app]

# Streamlit listen to this container port
EXPOSE 8501

# How to test if a container is still working
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run as executable
ENTRYPOINT ["streamlit", "run", "app_llm.py", "--server.port=8501", "--server.address=0.0.0.0"]

# # Creates a non-root user with an explicit UID and adds permission to access the /app folder
# # For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
# RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
# USER appuser

# # During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
# CMD ["python", "app.py"]
