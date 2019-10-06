FROM python:rc-alpine
WORKDIR /app

RUN apk --no-cache add ca-certificates curl tar &&\
    curl -sL https://github.com/swoiow/tmp_example/archive/oauth_server.tar.gz | tar -xz -C . --strip-components=1


FROM python:rc-alpine

ADD https://github.com/Yelp/dumb-init/releases/download/v1.2.2/dumb-init_1.2.2_amd64 /usr/local/bin/dumb-init
RUN chmod +x /usr/local/bin/dumb-init

WORKDIR /app
COPY --from=0 /app .

ENV REDIS=localhost

RUN set -ex \
    && pip install --no-cache-dir -q -r requirements.txt \
    && python manage.py collectstatic

ENV DJANGO_SETTINGS_MODULE=oauth.settings_prod

ENTRYPOINT ["dumb-init", "--"]
