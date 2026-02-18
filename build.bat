@echo off
title package builder
echo building
python setup.py sdist bdist_wheel
echo press any key to upload
pause
py -m twine upload --repository pypi dist/*