# Use an official Python runtime as a parent image
FROM python:alpine

# Set the working directory to /app
WORKDIR /app

# Copy current directory contents into the container at /app
COPY . /app

# Make port 80 available to the world outside this container
EXPOSE 9999

# Run app.py when the container launches
CMD ["python", "naming.py", "9999"]
