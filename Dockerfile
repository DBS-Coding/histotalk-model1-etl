# 1. Base image
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /etl

# 3. Install git and other essential tools
RUN apt-get update && \
apt-get install -y --no-install-recommends git openssh-client && \
rm -rf /var/lib/apt/lists/*
# RUN apt-get update && \
#     apt-get install -y git && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*


# 4. Salin file dependency
COPY requirements-test.txt requirements-full.txt

# 5. Install dependencies
RUN pip install --no-cache-dir -r requirements-full.txt

# 6. Salin semua file ke dalam image
COPY . .

# 7. Tentukan perintah saat container dijalankan
CMD ["python", "full-etl.py"]
