#!/bin/bash

# This script initializes the Lost and Found application
# Make sure to run this script with permissions: chmod +x init.sh

echo "===== Initializing Lost and Found Application ====="

# Create required directories if they don't exist
echo "Creating required directories..."
mkdir -p static/css static/js media nginx

# Create Docker-related files
echo "Setting up docker files..."
touch requirements.txt Dockerfile docker-compose.yml

# Create Django project structure
echo "Creating Django project structure..."
mkdir -p lost_and_found core

# Check if all files were created
echo "Checking project structure..."
if [ -d "lost_and_found" ] && [ -d "core" ] && [ -d "static" ] && [ -d "nginx" ]; then
    echo "Project structure created successfully."
else 
    echo "There was an issue creating the project structure. Please check the error messages."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file with default values..."
    cat > .env << EOL
# Django configurations
DEBUG=True
SECRET_KEY=django-insecure-change-this-in-production-environment-very-important
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database configurations
DB_NAME=lost_and_found_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Minio configurations
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio123
MINIO_SERVER=minio:9000
MINIO_BUCKET_NAME=lost-and-found
MINIO_ACCESS_KEY=minio
MINIO_SECRET_KEY=minio123
MINIO_SECURE=False
EOL
    echo ".env file created with default values."
else
    echo ".env file already exists, skipping..."
fi

# Output next steps
echo ""
echo "===== Next Steps ====="
echo "1. Review the .env file and update values as needed"
echo "2. Build and start the application using Docker Compose:"
echo "   docker-compose up --build"
echo ""
echo "The application will be available at:"
echo "- Web interface: http://localhost"
echo "- Admin interface: http://localhost/admin"
echo "- API endpoints: http://localhost/api"
echo "- Minio console: http://localhost:9001"
echo ""
echo "Enjoy using Lost and Found Application!"