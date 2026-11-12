.PHONY: setup dev check demo evaluate evaluate-real evaluate-real-v2
setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install -r requirements-dev.lock
	.venv/bin/python -m pip install --no-deps -e .
	cd web && npm ci
dev:
	.venv/bin/python scripts/dev.py
check:
	.venv/bin/ruff check src tests scripts
	.venv/bin/ruff format --check src tests scripts
	.venv/bin/mypy src
	.venv/bin/pytest
	cd web && npm run build
demo:
	.venv/bin/codeimpact --demo
evaluate:
	.venv/bin/python -m codeimpact.evaluate --corpus corpus/cases --output reports/corpus-evaluation.json
evaluate-real:
	.venv/bin/python -m codeimpact.real_evaluate --corpus corpus/real --output reports/real-evaluation.json
evaluate-real-v2:
	.venv/bin/python -m codeimpact.fresh_evaluate --corpus corpus/real-v2 --output reports/real-v2-evaluation.json
