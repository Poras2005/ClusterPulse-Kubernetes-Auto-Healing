FROM python:3.12-slim
WORKDIR /app
# Copy requirements from root to workdir
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy the entire controller directory content into /app
COPY controller/ .
# Run the controller
CMD ["python3", "main.py"]
