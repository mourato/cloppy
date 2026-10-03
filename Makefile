.DEFAULT_GOAL := build
.PHONY: build package
build:
	"$(CURDIR)/Scripts/build-cloppy.sh"
package: build
	ditto -c -k --sequesterRsrc --keepParent "$(CURDIR)/build/Cloppy.app" "$(CURDIR)/build/Cloppy.zip"
