FROM python:3.7-buster

# Environment variables
ENV PHANTOM_JS_VERSION ${PHANTOM_JS_VERSION:-2.1.1-linux-x86_64}
ENV PHANTOMJS_EXE="/usr/local/bin/phantomjs"
ENV PHANTOMJS_ARGS="--disk-cache=true,--max-disk-cache-size=50000,--disk-cache-path=/tmp/,--load-images=true,--ignore-ssl-errors=true,--ssl-protocol=any"
ENV PHANTOMJS_TIME_ZONE="UTC"
ENV PHANTOMJS_TIMEOUT_INITIAL=20
ENV PHANTONJS_TIMEOUT_PAGE_LOAD=15
ENV PHANTOMJS_TIMEOUT_RENDER_RESPONSE=15
ENV PHANTOMJS_TIMEOUT_STARTUP=20
ENV PHANTOMJS_RESOURCE_WAIT_MS=300
ENV PHANTOMJS_LIFETIME_IDLE_SHUTDOWN_SEC=300
ENV PHANTOMJS_LIFETIME_MAX_LIFETIME_SEC=1800

# Install necessary tools
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        bzip2 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Install PhantomJS
RUN mkdir /tmp/phantomjs \
 && curl -Ls https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-${PHANTOM_JS_VERSION}.tar.bz2 \
        | tar -xj --strip-components=1 -C /tmp/phantomjs \
 && mv /tmp/phantomjs/bin/phantomjs ${PHANTOMJS_EXE} \
 && rm -r /tmp/phantomjs

# Add PhantomJS to the path
ENV PATH="${PHANTOMJS_EXE}:${PATH}"

# Install python requirements
COPY docker/requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt \
 && rm requirements.txt

# Install phantom-snap
COPY phantom_snap /phantom_snap

# Apply openssl modification for buster
COPY docker/openssl.cnf /etc/ssl/openssl.cnf

# Install runtime files
COPY docker/main.py /
COPY docker/render.py /

ENTRYPOINT ["uvicorn","--host","0.0.0.0","--port","8080","main:app"]
