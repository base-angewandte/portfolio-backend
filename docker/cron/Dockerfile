FROM alpine:3.10.0
ENV TZ Europe/Vienna

# Timezone
RUN apk add --no-cache tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

RUN apk add --no-cache docker

COPY crontab /tmp/crontab

COPY run-crond.sh /run-crond.sh
RUN chmod +x /run-crond.sh

CMD ["/run-crond.sh"]
