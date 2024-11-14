#!/bin/sh
echo "Init migrations"
until alembic upgrade head
do
  echo "Waiting for init migrations..."
  sleep 2
done
exec "$@"
