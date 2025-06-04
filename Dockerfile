# 1. Base image
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /etl

# 3. Salin file dependency
COPY requirements-test.txt requirements-test.txt

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements-test.txt

# 5. Salin semua file ke dalam image
COPY . .

# 6. Tentukan perintah saat container dijalankan
CMD ["python", "testing-push.py"]