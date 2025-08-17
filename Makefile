deploy:
	docker compose -f docker-compose.yml up -d --build

run:
	uv run fastapi dev backend/main.py

up:
	dbmate up

new:
	dbmate new <migration_name>

down:
	dbmate down

status:
	dbmate status