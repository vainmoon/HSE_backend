.PHONY: up down logs train test worker

train:
	python scripts/train_model.py --path model.pkl

up:
	docker compose up --build -d

down:
	docker compose down

down-volumes:
	docker compose down -v

logs:
	docker compose logs -f

logs-%:
	docker compose logs -f $*

worker:
	python -m workers.moderation_worker

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=. --cov-report=term-missing
