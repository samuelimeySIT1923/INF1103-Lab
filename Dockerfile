FROM python:3.14-slim
RUN apk add --no-cache python3 g++ make
WORKDIR /app
COPY inventory_manager.py .
COPY inventory.json .
COPY . .
CMD ["python", "-u", "inventory_manager.py"]