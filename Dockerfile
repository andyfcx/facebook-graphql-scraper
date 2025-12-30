# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome or Chromium (with modern repository key handling)
RUN mkdir -p /etc/apt/keyrings \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg \
    && chmod 644 /etc/apt/keyrings/google-chrome.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && { apt-get install -y google-chrome-stable || apt-get install -y chromium || apt-get install -y chromium-browser; } \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN if command -v google-chrome > /dev/null; then \
        CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1) \
        && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION") \
        && wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"; \
    elif command -v chromium > /dev/null; then \
        CHROMIUM_VERSION=$(chromium --version | awk '{print $2}' | cut -d '.' -f 1) \
        && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROMIUM_VERSION") \
        && wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"; \
    else \
        echo "Neither Chrome nor Chromium is installed. Installing latest ChromeDriver." \
        && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE") \
        && wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"; \
    fi \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . .

# Set environment variable for chromedriver path
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Set display port to avoid crash
ENV DISPLAY=:99

# Create a modified example script that uses the environment variable
RUN sed -i 's|driver_path = "[^"]*"|driver_path = os.environ.get("CHROMEDRIVER_PATH")|g' fb_graphql_scraper/example.py && \
    sed -i '1s|^|import os\n|' fb_graphql_scraper/example.py

# Command to run when container starts
CMD ["python", "-m", "fb_graphql_scraper.example"]