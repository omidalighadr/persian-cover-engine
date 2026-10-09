.PHONY: install check test fmt examples docker

install:
	pip install -e ".[dev,fallback-shaping]"

check:
	ruff check .
	ruff format --check .
	mypy

test:
	pytest -q

fmt:
	ruff format .
	ruff check --fix .

examples:
	persian-cover "چطور با هوش مصنوعی مقاله بنویسیم؟" --subtitle "راهنمای گام‌به‌گام برای ۱۰ دقیقه" \
		--highlight "هوش" --handle "@example" --out examples/post-teal.png
	persian-cover "راهنمای کامل ۱۲۳ ابزار" --subtitle "فهرست بررسی‌شده" --palette ivory \
		--size story --highlight "ابزار" --out examples/story-ivory.png
	persian-cover "Designing reliable queues" --subtitle "Backend notes" --palette midnight \
		--background linear --outline --size wide --highlight reliable --out examples/wide-midnight.png

docker:
	docker build -t persian-cover-engine .
