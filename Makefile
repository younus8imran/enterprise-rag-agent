.PHONY: build up down restart test lint type-check evaluate

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

test:
	pytest tests/

lint:
	flake8 app tests

type-check:
	mypy app tests

evaluate:
	export PYTHONPATH=$PYTHONPATH:. && .venv/bin/python tests/evaluation/run_evaluation.py
