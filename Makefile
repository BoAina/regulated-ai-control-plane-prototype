.PHONY: test lint coverage clean

test:
	python3 -m pytest tests/ -v

coverage:
	python3 -m pytest tests/ -v --cov=src --cov-report=term --cov-fail-under=80

lint:
	python3 -m flake8 src/ tests/ --max-line-length 120

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
