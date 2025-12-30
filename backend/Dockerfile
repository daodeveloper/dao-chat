FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/data/faiss_index

COPY app/ /app/app/
COPY data/ /app/data/

RUN chmod -R 755 /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]