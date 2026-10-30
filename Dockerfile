FROM python:3.14-slim

WORKDIR /app
COPY inventory_manager.py .
COPY inventory.json .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "inventory_manager.py"]