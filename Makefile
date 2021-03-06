.PHONY: all virtualenv

virtualenv: ./env/requirements.built

env:
	virtualenv env

./env/requirements.built: env requirements.txt
	./env/bin/pip install -r requirements.txt
	cp requirements.txt ./env/requirements.built

flake8:
	flake8 --max-line-length=110 hal plugins adapters *.py
