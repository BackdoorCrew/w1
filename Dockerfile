# w1/Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.11.5-slim

# Set environment variables to prevent Python from writing .pyc files to disc or buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the Django settings module environment variable
ENV DJANGO_SETTINGS_MODULE=w1.settings

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy your custom Python scripts into the container
COPY ./create_dev_admin.py /app/create_dev_admin.py
COPY ./docker_entrypoint.py /app/docker_entrypoint.py

# Make your Python scripts executable
# (create_dev_admin.py is called by the entrypoint script using 'python create_dev_admin.py',
# so it doesn't strictly need +x here, but it's not harmful.
# docker_entrypoint.py is also called with 'python /app/docker_entrypoint.py', so +x isn't strictly
# required for that invocation either, but good practice if you ever wanted to call it directly
# and it had a shebang.)
RUN chmod +x /app/create_dev_admin.py && \
    chmod +x /app/docker_entrypoint.py

# Copy the rest of the application's code into the container
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput --clear

# Expose port 8000 (Gunicorn will listen on the $PORT provided by Railway,
# this EXPOSE is more for documentation or local Docker runs without $PORT)
EXPOSE 8000

# Define the entrypoint for the container.
# This will run your Python script when the container starts.
ENTRYPOINT ["python", "/app/docker_entrypoint.py"]

# Define the default command to be passed to the entrypoint.
# Your docker_entrypoint.py script will receive these arguments.
# Gunicorn will bind to 0.0.0.0 and automatically use the $PORT environment
# variable provided by Railway (or similar PaaS).
CMD ["gunicorn", "w1.wsgi:application", "--bind", "0.0.0.0", "--workers", "1", "--threads", "1", "--worker-class", "gthread", "--log-level", "info"]