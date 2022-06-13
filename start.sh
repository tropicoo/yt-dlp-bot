#!/bin/bash

check_reachability() {
while ! nc -z "$1" "${!2}"
do
  echo "Waiting for $3 to be reachable on port ${!2}"
  sleep 1
done
echo "Connection to $3 on port ${!2} verified"
return 0
}


wait_for_services_to_be_reachable() {
  check_reachability rabbitmq RABBITMQ_PORT RabbitMQ
  check_reachability postgres POSTGRES_PORT PostgreSQL
}

wait_for_services_to_be_reachable
exit 0
