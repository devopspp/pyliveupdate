all:
	python setup.py sdist bdist_wheel

publish:
	python setup.py sdist bdist_wheel
	twine upload dist/*

clean:
	rm -r dist/

