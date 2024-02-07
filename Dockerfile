FROM python:3.12-slim

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -e .

EXPOSE 9547

ENTRYPOINT ["kea-exporter"]
