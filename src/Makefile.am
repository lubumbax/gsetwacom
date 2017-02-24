## Process this file with automake to produce Makefile.in
## Created by Anjuta


uidir = $(pkgdatadir)/ui
ui_DATA = w_main.ui \
	w_stylus.ui \
	w_mapping.ui \
	w_info.ui


## The main script
bin_SCRIPTS = gsetwacom.py

## Directory where .class files will be installed
gsetwacomdir = $(pythondir)/gsetwacom


gsetwacom_PYTHON = \
	gsetwacom.py \
	w_main.py \
	scanner.py \
	registry.py \
	libwrapper.py \
	device.py \
	error.py \
	logger.py \
	libwacom.py


EXTRA_DIST = $(ui_DATA)


# Remove ui directory on uninstall
uninstall-local:

	-rm -r $(uidir)

	-rm -r $(pkgdatadir)
