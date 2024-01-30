compile-deps:
	pip-compile requirements.in -q --no-emit-index-url
	pip-compile requirements.dev.in -q --no-emit-index-url
install-dev-deps: compile-deps
	pip install -r requirements.dev.txt