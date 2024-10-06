#!/bin/sh
echo "Starting memcached"
until /etc/init.d/memcached start
do
  echo "Waiting for memcached to be ready..."
  sleep 2
done
echo "Init migrations"
until poetry run alembic upgrade head
do
  echo "Waiting for init migrations..."
  sleep 2
done
echo "Creating migrations"
until poetry run alembic revision --autogenerate
do
  echo "Waiting for create migrations..."
  sleep 2
done
echo "Applying migrations"
until poetry run alembic upgrade head
do
  echo "Waiting for apply migrations..."
  sleep 2
done
exec "$@"
