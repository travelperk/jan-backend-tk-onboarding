compile-deps:
	pip-compile requirements.in -q
	pip-compile requirements.dev.in -q
install-dev-deps: compile-deps
	pip install -r requirements.dev.txt