.PHONY: setup run benchmark clean

setup:
	@chmod +x setup.sh
	@./setup.sh

run:
	@venv/bin/python -m src.main

benchmark:
	@venv/bin/python scripts/run_benchmarks.py

clean:
	@echo "🧹 Cleaning up..."
	@rm -rf venv
	@rm -rf data/*.json
	@rm -rf data/*.index
	@rm -rf logs/*.jsonl
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "✅ Cleaned."
