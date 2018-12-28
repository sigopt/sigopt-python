.PHONY: test lint

test:	export PYTHONPATH=.
test:
	@python -m pytest -rw -v test

lint:
	@./lint

update:
	@pip install -r requirements-dev.txt
	@pip install -r requirements.txt
	@python setup.py clean --all
	@pip install -e .\[dev\]
