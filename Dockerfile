FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ai_manager.py data_manager.py io_manager.py logic_manager.py ./
COPY tests/ tests/
COPY data/ data/

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "io_manager.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]