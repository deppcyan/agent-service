FROM nvidia/cuda:12.8.0-devel-ubuntu22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    python3.10-venv \
    software-properties-common \
    ffmpeg \
    openssh-server \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install fluentd and its dependencies
RUN apt-get update && apt-get install -y \
ruby \
ruby-dev \
build-essential \
&& rm -rf /var/lib/apt/lists/* \
&& gem install fluentd --no-doc \
&& gem install fluent-plugin-s3 --no-doc

# Create fluentd configuration directory
RUN mkdir -p /etc/fluent
COPY fluent/fluent.conf /etc/fluent/fluent.conf
RUN mkdir -p /var/log/fluent

# Instead of copying the Conda environment, we'll create a new Python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --index-url https://pypi.mirrors.ustc.edu.cn/simple/

COPY app app
COPY config config

COPY start.sh start.sh
RUN mkdir -p /app/log

EXPOSE 8000

# Command to run the application
CMD ["/bin/bash", "start.sh"]