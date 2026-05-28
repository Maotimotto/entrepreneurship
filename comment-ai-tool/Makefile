.PHONY: run test test-edge clean

run:
	python3 -m src.main

test:
	python3 test_api.py

test-edge:
	python3 test_edge.py

test-all: test test-edge

clean:
	rm -f comment_ai.db
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
