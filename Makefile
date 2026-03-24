.PHONY: setup dev stop clean test migrate seed shell

setup:
	@echo "Setting up Upstream Literacy E-Commerce..."
	cp -n .env.example .env 2>/dev/null || true
	docker compose build
	docker compose run --rm backend python manage.py migrate
	docker compose run --rm backend python manage.py seed_products
	docker compose run --rm backend python manage.py createsuperuser --noinput || true
	@echo ""
	@echo "Setup complete. Run 'make dev' to start all services."
	@echo "  Backend:  http://localhost:8001"
	@echo "  Frontend: http://localhost:5199"
	@echo "  Admin:    http://localhost:8001/admin/"
	@echo "  Login:    admin@upstream.dev / admin123!"

dev:
	docker compose up

stop:
	docker compose down

clean:
	docker compose down -v
	docker compose build --no-cache

test:
	docker compose run --rm backend pytest
	docker compose run --rm frontend npm test

migrate:
	docker compose run --rm backend python manage.py migrate

seed:
	docker compose run --rm backend python manage.py seed_products

shell:
	docker compose run --rm backend python manage.py shell
