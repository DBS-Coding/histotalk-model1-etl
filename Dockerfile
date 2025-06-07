# 1. Base image
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /etl

# 3. Install git and other essential tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends git openssh-client build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    apt-get autoremove -y build-essential 

# 4. Salin file dependency
COPY r-test.txt r-test.txt

# 5. Install dependencies
RUN pip install --no-cache-dir -r r-test.txt

# 6. Salin semua file ke dalam image
COPY . .

# 7. Tentukan perintah saat container dijalankan
CMD ["python", "testing.py"]