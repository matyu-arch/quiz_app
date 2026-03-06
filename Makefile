.PHONY: lint format test check

lint:  ## Ruff による静的解析
	uv run ruff check src/ tests/

format:  ## Ruff によるフォーマット
	uv run ruff format src/ tests/

test:  ## pytest 実行
	uv run pytest

check: lint format test  ## 全品質ゲートの実行
	@echo "✅ All checks passed!"
