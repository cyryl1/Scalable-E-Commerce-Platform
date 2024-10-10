# Docker file for User service
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the requirements file.
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask app code
COPY . .

# Expose the port Flask is running on (e.g., 5000)
EXPOSE 5005

# Command to run the Flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5005"]