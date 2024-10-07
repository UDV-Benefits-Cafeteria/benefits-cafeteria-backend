# benefits-cafeteria-backend

## Requirements

- [Python 3.12+](https://www.python.org/downloads/)
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/UDV-Benefits-Cafeteria/benefits-cafeteria-backend.git
cd benefits-cafeteria-backend
```
### 2. Set up the ``.env`` file

Create a ``.env`` file in the root of your project and define your environment variables. Here is an example:

```dotenv
DEBUG=debugpy
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
POSTGRES_PORT=5432
POSTGRES_HOST=db
SECRET_KEY=some_secret_key
FLOWER_LOGIN=admin
FLOWER_PASSWORD=admin
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq//
CELERY_RESULT_BACKEND=rpc://
```

### 3. Set up Docker
Make sure you have Docker installed. Then, build and run the Docker containers.

```bash
docker-compose -f .\docker-compose-dev.yml up -d --build
```
This command will:
1. Build the Docker images
2. Start the containers defined in the ``docker-compose-dev.yml`` file

```bash
docker-compose -f .\docker-compose-dev.yml down
```
This command will:
1. Stop the docker containers

### 4. Access the application
After the containers are up and running, the FastAPI app will be accessible at ``http://localhost:8000``.

The auto-generated API documentation will be available at:

- Swagger UI: ``http://localhost:8000/docs``
- Redoc: ``http://localhost:8000/redoc``

# Testing

To run tests, you can use the following command inside the Docker dev container:
```bash
docker exec app poetry run pytest tests/
```
Or, if you're not using Docker (you need to install postgres and create virtualenv): 
```bash
poetry run pytest tests/
```

# Linting, code checking and etc.
To run pre commit hook use following command:

```bash
pre-commit run --all-files
```

# Project Structure

```
├── src
│   ├── config.py             # Main config file
│   ├── main.py               # Main FastAPI application
│   ├── api
│   │   └── v1                # Routers
│   ├── db                    
│   ├── models               
│   ├── repositories
│   ├── schemas
│   ├── services
│   └── utils
│
├── tests
│   ├── conftest.py
│   └── test_*.py    
│               
├── Dockerfile.dev            # Docker development configuration
├── Dockerfile.prod           # Docker production configuration
├── docker-compose-dev.yml    # Docker Compose development configuration
├── docker-compose-prod.yml   # Docker Compose production configuration
├── example.env               # Environment variables
├── entrypoint.sh             # Entrypoint file for docker
├── .gitignore                # Gitignore file for project
├── setup.cfg                 # Setup file only for flake8 now
├── pyproject.toml            # Main poetry file
├── poetry.lock               # Poetry dependencies lock file
├── .pre-commit-config.yaml   # Pre-commit for this project
└── README.md                 # This file
```
