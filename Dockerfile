FROM python:3.14-slim

WORKDIR /app
COPY inventory_manager.py .
COPY inventory.json .
CMD ["python", "inventory_manager.py"]
ENTRYPOINT ["python", "-u", "inventory_manager.py"]