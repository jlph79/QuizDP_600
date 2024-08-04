# Use the official Python image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Set the PORT environment variable
ENV PORT=3000

# Expose the specified port
EXPOSE $PORT

# Command to run the application
CMD ["streamlit", "run", "main.py", "--server.port=$PORT", "--server.address=0.0.0.0"]

HEALTHCHECK CMD curl --fail http://localhost:$PORT/ || exit 1
