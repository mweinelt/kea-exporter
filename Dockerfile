FROM python:3.12-slim

LABEL org.opencontainers.image.title=kea-exporter
LABEL org.opencontainers.image.description="Prometheus Exporter for the ISC Kea DHCP Server"
LABEL org.opencontainers.image.authors="Martin Weinelt <hexa@darmstadt.ccc.de>"
LABEL org.opencontainers.image.url=https://github.com/mweinelt/kea-exporter
LABEL org.opencontainers.image.licenses=MIT

RUN groupadd -g 1000 kea-exporter && useradd -m -u 1000 -g 1000 kea-exporter

ENV PATH="/home/kea-exporter/.local/bin:${PATH}"

WORKDIR /usr/src/app

RUN chown -R kea-exporter:kea-exporter /usr/src/app

USER 1000:1000

COPY . .

RUN pip install --user --no-cache-dir -e .

EXPOSE 9547

ENTRYPOINT ["kea-exporter"]
