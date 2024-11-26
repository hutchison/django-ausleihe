.PHONY: build upload clean

build: clean
	@( \
		. venv/bin/activate; \
		python3 -m build; \
	)

clean:
	rm -Rf django_ausleihe.egg-info/
	rm -Rf build
	rm -Rf dist

upload:
	twine upload dist/*
