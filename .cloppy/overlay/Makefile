.DEFAULT_GOAL := help
.PHONY: help build install update package check
help:
	@printf '%s\n' \
	    'Cloppy commands:' \
	    '  make help     Show available commands (default)' \
	    '  make build    Build and validate build/Cloppy.app' \
	    '  make install  Build and install /Applications/Cloppy.app' \
	    '  make update   Import and review the latest stable Clop release' \
	    '  make package  Build and create build/Cloppy.zip' \
	    '  make check    Run workflow and patch-queue tests' \
	    '  make hooks    Enable versioned Git hooks for this clone'
build:
	"$(CURDIR)/Scripts/build-cloppy.sh"
install: build
	"$(CURDIR)/Scripts/install-cloppy.sh"
update:
	python3 "$(CURDIR)/Scripts/update-cloppy.py"
package: build
	ditto -c -k --sequesterRsrc --keepParent "$(CURDIR)/build/Cloppy.app" "$(CURDIR)/build/Cloppy.zip"
check:
	PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "$(CURDIR)/tests" -p 'test_*.py'

.PHONY: hooks
hooks:
	@git config --local core.hooksPath .githooks
	@echo "Git LFS hooks enabled; merges on main/master push, then clean merged worktrees"
