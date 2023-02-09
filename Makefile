update:
	git pull origin main

push:
	git add -A 
	git commit -m "Automated Commit $(shell date --iso=seconds)"
	git push origin main

image:
	pyrcc5 resources.qrc -o images.py
