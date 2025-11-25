# Use an official Python 3.10 image
FROM python:3.10-slim

# Set the working folder inside the container
WORKDIR /app

# Copy and install the requirements
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy the rest of the app's code
COPY . .

# Run the Uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]