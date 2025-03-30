MAKEFLAGS += --silent

OPTIONS ?= --build --remove-orphans #--force-recreate
APP ?= app

.PHONY: docker healthcheck sync test clean

docker:
	docker-compose up $(OPTIONS) -d

%:
	docker-compose up $(OPTIONS) $@ -d
	docker-compose ps -a

healthcheck:
	docker inspect $(APP) --format "{{ (index (.State.Health.Log) 0).Output }}"

sync:
	uv sync

test:
	PYTHONPATH=. uv run pytest tests

clean:
	docker-compose down --remove-orphans -v --rmi local

-include .env
