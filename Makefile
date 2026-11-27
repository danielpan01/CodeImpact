.PHONY: setup dev check demo evaluate evaluate-real evaluate-real-v2 evaluate-real-v3 evaluate-real-v4 evaluate-real-v4-unittest evaluate-real-v4-variadic evaluate-real-v4-parameter-rows evaluate-real-v4-reexports evaluate-real-v5 evaluate-real-v5-equality evaluate-real-v5-factories evaluate-real-v5-first-assertion evaluate-real-v5-less-than evaluate-real-v5-inequality pilot benchmark serve verify-pilot
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
	.venv/bin/python -m codeimpact.evaluate --runtime-imports
evaluate-real:
	.venv/bin/python -m codeimpact.real_evaluate --corpus corpus/real --output reports/real-evaluation.json
evaluate-real-v2:
	.venv/bin/python -m codeimpact.fresh_evaluate --corpus corpus/real-v2 --output reports/real-v2-parameter-tables-v1-evaluation.json
evaluate-real-v3:
	.venv/bin/python -m codeimpact.holdout_evaluate --corpus corpus/real-v3 --output reports/real-v3-finite-string-guards-v1-evaluation.json
evaluate-real-v4:
	.venv/bin/python -m codeimpact.v4_evaluate
evaluate-real-v4-unittest:
	.venv/bin/python -m codeimpact.unittest_evaluate
evaluate-real-v4-variadic:
	.venv/bin/python -m codeimpact.variadic_evaluate
evaluate-real-v4-parameter-rows:
	.venv/bin/python -m codeimpact.parameter_rows_evaluate
evaluate-real-v4-reexports:
	.venv/bin/python -m codeimpact.explicit_reexports_evaluate
evaluate-real-v5:
	.venv/bin/python -m codeimpact.v5_evaluate
evaluate-real-v5-equality:
	.venv/bin/python -m codeimpact.equality_evaluate
evaluate-real-v5-factories:
	.venv/bin/python -m codeimpact.factory_evaluate
evaluate-real-v5-first-assertion:
	.venv/bin/python -m codeimpact.first_assertion_evaluate
evaluate-real-v5-less-than:
	.venv/bin/python -m codeimpact.less_than_evaluate
evaluate-real-v5-inequality:
	.venv/bin/python -m codeimpact.inequality_evaluate
pilot:
	.venv/bin/python scripts/prepare_pilot.py
benchmark:
	.venv/bin/python scripts/benchmark.py
serve:
	cd web && npm run build
	.venv/bin/python -m codeimpact.serve
verify-pilot:
	.venv/bin/python scripts/verify_pilot.py
