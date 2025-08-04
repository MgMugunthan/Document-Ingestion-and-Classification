# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs routed/invoices routed/others routed/receipts routed/resumes

# Set environment variables
ENV PYTHONPATH=/app

# Command to run the router
CMD ["python", "router.py"]
