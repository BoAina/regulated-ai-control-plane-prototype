.PHONY: test lint clean

test:
	python3 -m pytest tests/ -v

lint:
	python3 -m flake8 src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
