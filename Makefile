

default: lint test

setup:
	./setup_virtualenv

run:
	python control.py 2>&1

lint:
	pylint --rcfile pylintrc *.py helper/*.py

test:
	python -m unittest discover

clean:
	find . -iname \*.pyc -print0 | xargs -0r rm
	rm -rf bin include lib local
