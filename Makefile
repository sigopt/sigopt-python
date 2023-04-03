.PHONY: test lint integration_test vulture vulture-allowlist

test:
	@PYTHONPATH=. python -m pytest -rw -v test

integration_test:
	@PYTHONPATH=. python -m pytest -rw -v integration_test

vulture:
	@./tools/run_vulture.sh . .vulture_allowlist

vulture-allowlist:
	@./tools/generate_vulture_allowlist > .vulture_allowlist

update:
	@python setup.py clean --all
	@pip install -e '.[all]'
