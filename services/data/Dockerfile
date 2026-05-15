FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# shared/ is mounted as a volume in docker-compose.yml
# so it does not need to be COPY'd here

COPY main.py .

CMD ["python", "main.py"]
