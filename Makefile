.DEFAULT_GOAL := build
.PHONY: build install update package check
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
