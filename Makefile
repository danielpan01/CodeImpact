.PHONY: setup dev check demo evaluate evaluate-real evaluate-real-v2 evaluate-real-v3 pilot benchmark serve verify-pilot
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
	.venv/bin/python -m codeimpact.fresh_evaluate --corpus corpus/real-v2 --output reports/real-v2-parameter-tables-v1-evaluation.json
evaluate-real-v3:
	.venv/bin/python -m codeimpact.holdout_evaluate --corpus corpus/real-v3 --output reports/real-v3-parameter-tables-v1-evaluation.json
pilot:
	.venv/bin/python scripts/prepare_pilot.py
benchmark:
	.venv/bin/python scripts/benchmark.py
serve:
	cd web && npm run build
	.venv/bin/python -m codeimpact.serve
verify-pilot:
	.venv/bin/python scripts/verify_pilot.py
