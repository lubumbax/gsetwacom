## Process this file with automake to produce Makefile.in
## Created by Anjuta


uidir = $(pkgdatadir)/ui
ui_DATA = gsetwacom.ui \
	wacom-stylus-page.ui \
	w_main.ui


## The main script
bin_SCRIPTS = gsetwacom.py

## Directory where .class files will be installed
gsetwacomdir = $(pythondir)/gsetwacom


gsetwacom_PYTHON = \
	gsetwacom.py \
	w_main.py \
	scanner.py \
	registry.py \
	logger.py \
	mapper.py \
	libwacom.py \
	libwrapper.py \
	device.py \
	error.py


EXTRA_DIST = $(ui_DATA)


# Remove ui directory on uninstall
uninstall-local:

	-rm -r $(uidir)

	-rm -r $(pkgdatadir)
