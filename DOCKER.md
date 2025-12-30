# Docker Setup for Facebook GraphQL Scraper

This document explains how to use the Docker container for the Facebook GraphQL Scraper project.

## Prerequisites

- [Docker](https://www.docker.com/get-started) installed on your system

## Building the Docker Image

To build the Docker image, run the following command from the project root directory:

```bash
docker build -t facebook-graphql-scraper .
```

## Running the Container

### Basic Usage

To run the container with the default example script:

```bash
docker run facebook-graphql-scraper
```

### Custom Usage

To run the container with your own Facebook credentials and target:

1. Create a custom script or modify the example.py file
2. Mount your script into the container:

```bash
docker run -v $(pwd)/your_script.py:/app/your_script.py facebook-graphql-scraper python /app/your_script.py
```

## Environment Variables

The following environment variables can be set when running the container:

- `CHROMEDRIVER_PATH`: Path to the chromedriver executable (default: `/usr/local/bin/chromedriver`)
- `DISPLAY`: Display setting for Chrome (default: `:99`)

Example:

```bash
docker run -e DISPLAY=:0 facebook-graphql-scraper
```

## Notes

- The container attempts to install Google Chrome, with fallbacks to Chromium or chromium-browser if Chrome is not available for your architecture
- ChromeDriver is installed with a version matching your installed browser
- The container is compatible with both x86_64 (amd64) and ARM architectures (e.g., Apple Silicon)
- Repository keys are handled using the modern approach (no apt-key deprecation warnings)
- selenium-wire is installed, which requires both selenium and a Chrome/Chromium browser
- The container runs in headless mode by default