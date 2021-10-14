.PHONY: test lint

test:
	@PYTHONPATH=. python -m pytest -rw -v test

lint:
	@./lint

update:
	@git submodule init
	@git submodule update
	@pip install -r requirements-dev.txt
	@pip install -r requirements.txt
	@python setup.py clean --all
	@pip install -e .\[dev\]
