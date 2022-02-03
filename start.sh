#!/bin/bash

while ! nc -z rabbitmq "${RABBITMQ_PORT}"
do
  echo "Waiting for RabbitMQ to be reachable on port ${RABBITMQ_PORT}"
  sleep 1
done

echo "Connection to RabbitMQ on port ${RABBITMQ_PORT} verified"
exit 0
