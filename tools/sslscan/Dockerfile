FROM alpine:3.19

RUN apk add --no-cache openssl git gcc musl-dev openssl-dev make && \
    apk add --no-cache --repository https://dl-cdn.alpinelinux.org/alpine/edge/testing sslscan || \
    { git clone --depth 1 https://github.com/rbsec/sslscan.git /tmp/sslscan && \
      cd /tmp/sslscan && make static && make install && rm -rf /tmp/sslscan; }

WORKDIR /data

ENTRYPOINT ["sslscan"]
