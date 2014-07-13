

default: lint test

setup:
	./setup_virtualenv

lint:
	bin/pylint --rcfile pylintrc *.py helper/*.py

test:
	bin/python -m unittest discover

clean:
	find . -iname \*.pyc -print0 | xargs -0r rm
	rm -rf bin include lib local

remote:
	rsync -avPh --delete \
          --exclude bin --exclude include --exclude lib --exclude local \
          --exclude \*.pyc --exclude .idea  \
	  ./ ${REMOTE}:test/
