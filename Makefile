.PHONY: build upload

build:
	@( \
		. venv/bin/activate; \
		python3 -m build; \
		rm -Rf build; \
	)

upload:
	twine upload dist/*
