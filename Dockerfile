# Use an official Python runtime as a parent image.
FROM python:3.9-slim

# Set the working directory in the container.
WORKDIR /app

# Copy the requirements file and install dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Expose the ports used by the application.
# Each container can use the same internal port because they run in isolated environments.
EXPOSE 5000

# Define the command to run your application.
CMD ["python", "main.py"]
