.PHONY: test lint integration_test

test:
	@PYTHONPATH=. python -m pytest -rw -v test

integration_test:
	@PYTHONPATH=. python -m pytest -rw -v integration_test

lint:
	@./lint

update:
	@pip install -r requirements-dev.txt
	@pip install -r requirements.txt
	@python setup.py clean --all
	@pip install -e .\[dev\]
