FROM python:3.14-slim

WORKDIR /app
COPY inventory_manager.py .
COPY inventory.json .
COPY . .
CMD ["python", "-u", "inventory_manager.py"]