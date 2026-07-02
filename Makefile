.PHONY: smoke test

smoke:
	python3 services/billing-service/billing.py
	python3 services/tenant-manager/db.py
	python3 services/vector-service/search.py

test:
	python3 -m unittest discover -s tests -v
