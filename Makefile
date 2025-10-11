.PHONY: install run test seed clean

install:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

run:
	. .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	. .venv/bin/activate && pytest -v

seed:
	. .venv/bin/activate && python3 -m app.seed_demo

clean:
	rm -rf .venv
	rm -f btc_crowdfund.db
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
