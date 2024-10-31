
FROM python:3.12-alpine
ENV TZ=Asia/Bangkok

WORKDIR /app

COPY requirements.txt cron.py ./
COPY crontab /tmp/crontab

RUN pip install --no-cache-dir -r requirements.txt \
    && crontab /tmp/crontab \
    && rm -rf /tmp/crontab

CMD ["/usr/sbin/crond", "-f", "-d", "5"]
