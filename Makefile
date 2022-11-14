.PHONY: build upload

build:
	@rm -Rf dist build
	python3 setup.py sdist bdist_wheel

upload:
	twine upload dist/*
