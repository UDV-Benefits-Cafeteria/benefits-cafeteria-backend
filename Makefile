PROJECT_NAME=UDV-Cafeteria-Backend
DOCKER_COMPOSE_FILE=docker-compose-dev.yml
DOCKER_COMPOSE_FILE_TESTS=docker-compose-tests.yml

up:
	@echo "🚀 Запуск приложения..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) up -d --build

down:
	@echo "🛑 Остановка приложения..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) down

build:
	@echo "🏗️ Сборка образов..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) build

restart:
	@echo "🔄 Перезапуск приложения..."
	$(MAKE) down
	$(MAKE) build
	$(MAKE) up

upapp:
	@echo "🚀 Запуск контейнера app..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) up --no-deps -d app

downapp:
	@echo "🛑 Остановка контейнера app..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) down app

buildapp:
	@echo "🏗️ Сборка образа app..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) build app

ra:
	@echo "🔄 Перезапуск контейнера app..."
	$(MAKE) downapp
	$(MAKE) buildapp
	$(MAKE) upapp

logs:
	@echo "📜 Просмотр логов приложения..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f

test:
	@echo "🧪 Запуск тестов..."
	docker-compose -f $(DOCKER_COMPOSE_FILE_TESTS) up -d --build 

shell:
	@echo "💻 Подключение к контейнеру приложения..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) exec app /bin/sh

clean:
	@echo "🧹 Очистка остановленных контейнеров и неиспользуемых данных..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) down --volumes --remove-orphans
	docker system prune -f

# Помощь
help:
	@echo "Доступные команды:"
	@echo "  make up        - Запуск приложения"
	@echo "  make down      - Остановка приложения"
	@echo "  make build     - Сборка Docker-образов"
	@echo "  make restart   - Перезапуск приложения"
	@echo "  make upapp     - Запуск контейнера app"
	@echo "  make downapp   - Остановка контейнера app"
	@echo "  make buildapp  - Сборка Docker-образа app"
	@echo "  make ra        - Перезапуск контейнера app"
	@echo "  make logs      - Просмотр логов"
	@echo "  make test      - Запуск тестов через pytest"
	@echo "  make shell     - Подключение к контейнеру app приложения"
	@echo "  make clean     - Очистка неиспользуемых данных"