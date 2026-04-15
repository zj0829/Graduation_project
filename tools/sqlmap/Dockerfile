FROM alpine:3.19

RUN apk add --no-cache python3 py3-pip git && \
    git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git /opt/sqlmap && \
    cd /opt/sqlmap && \
    pip3 install --no-cache-dir -r requirements.txt || true

WORKDIR /opt/sqlmap

ENTRYPOINT ["python3", "sqlmap.py"]
