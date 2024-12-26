FROM python:alpine3.19

WORKDIR /app

RUN apk add --no-cache gcc musl-dev openssl-dev

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/backup

VOLUME /app/backup

EXPOSE 5000

CMD ["python", "app.py"]
