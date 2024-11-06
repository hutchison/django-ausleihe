.PHONY: build upload

build:
	@( \
		. venv/bin/activate; \
		python3 -m build; \
	)

upload:
	twine upload dist/*
