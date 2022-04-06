.PHONY: test lint integration_test vulture vulture-allowlist

test:
	@PYTHONPATH=. python -m pytest -rw -v test

integration_test:
	@PYTHONPATH=. python -m pytest -rw -v integration_test

lint: vulture
	@./lint

vulture:
	@vulture --exclude "build,venv" --ignore-decorators "@click.*,@sigopt_cli.*,@pytest.*" . .vulture_allowlist

vulture-allowlist:
	@./tools/generate_vulture_allowlist > .vulture_allowlist

update:
	@pip install -r requirements-dev.txt
	@pip install -r requirements.txt
	@python setup.py clean --all
	@pip install -e .\[dev\]
