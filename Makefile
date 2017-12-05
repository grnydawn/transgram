PY ?=3

.PHONY: tests

test:
	cd tests && rm -f *.log
	cd tests && python${PY} -m unittest test_transgram

install:
	python${PY} setup.py install --user --record installed_files.txt

uninstall:
	cat installed_files.txt | xargs rm -rf
	rm -f installed_files.txt

init:
	pip install --user -r requirements.txt

clean:
	$(MAKE) -C docs clean
	rm -rf .cache build dist transgram.egg-info transgram.log
