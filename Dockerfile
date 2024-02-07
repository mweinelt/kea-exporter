FROM python:3.12-slim

RUN groupadd -g 1000 kea-exporter && useradd -m -u 1000 -g 1000 kea-exporter

WORKDIR /usr/src/app

RUN chown -R kea-exporter:kea-exporter /usr/src/app

USER 1000:1000

COPY . .

RUN pip install --user --no-cache-dir -e .

EXPOSE 9547

ENTRYPOINT ["python3", "-m", "kea_exporter"]
