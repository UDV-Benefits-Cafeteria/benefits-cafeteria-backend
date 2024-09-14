#!/bin/bash
echo "Starting memcached"
/etc/init.d/memcached start

if [ "$DEBUG" = "debugpy" ]
then
  echo "Running in debug mode"
  poetry run debugpy --listen 0.0.0.0:5678 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

elif [ "$DEBUG" = "pdb" ]
then
  echo "Running with PDB"
  poetry run uvicorn src.main:app --host=0.0.0.0 --reload

else
  echo "Running in production mode"
  poetry run uvicorn src.main:app --host=0.0.0.0 --reload
fi
