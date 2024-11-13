#!/bin/sh
echo "Init migrations"
until alembic upgrade head
do
  echo "Waiting for init migrations..."
  sleep 2
done
echo "Creating migrations"
until alembic revision --autogenerate
do
  echo "Waiting for create migrations..."
  sleep 2
done
echo "Applying migrations"
until alembic upgrade head
do
  echo "Waiting for apply migrations..."
  sleep 2
done
exec "$@"
