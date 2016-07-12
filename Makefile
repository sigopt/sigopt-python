.PHONY: pytest lint

pytest:	export PYTHONPATH=.
pytest:
	@python -m pytest -rw -v test

lint:
	@./lint
