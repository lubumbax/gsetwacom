#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*- 
#
# gsetwacom.py
# Copyright (C) 2017 Juan Carlos Muro <murojc@gmail.com>
# 
# GSetWacom is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# GSetWacom is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GdkPixbuf, Gdk
from argparse import ArgumentParser

import os
import sys

from error import GsException
from logger import Logger
from registry import DeviceRegistry
from device import DeviceBroker
from scanner import DeviceScanner
from w_main import WMain


def main(argv):
	
	args = get_arguments()
	#TODO: test the "device_database" option.

	if args.debug: 
		args.loglevel = 'debug'

	logger = Logger(args.loglevel)
	
	try:
		logger.info("Initializing the application")
		app = GSetWacom(logger, args)
	except GsException as ge:	
		logger.error("Couldn't initialize the application")
		return 1		

	logger.info("Running the application")
	if not app.run():
		logger.error('Terminating the application due to an irrecoverable error')
		return 1

	logger.info("Application terminated")
	return 0
	
def is_valid_device_file(parser, arg):
	# TODO: it is considered better practice to try and open the file with a try-except block, than to check for existence
	# try: ... except IOError
	if not os.path.exists(arg):
		parser.error("The device file %s does not exist!" % arg)
	else:
		return arg

def is_valid_device_database(parser, arg):
	# TODO: it is considered better practice to try and open the file with a try-except block, than to check for existence
	# try: ... except IOError
	if not glob.glob('%s/*.tablet' % arg) or not os.path.exists('%s/libwacom.stylus' % arg):
		parser.error("There is no libwacom database at %s!" % arg)
	else:
		return arg

def get_arguments():
	parser = ArgumentParser(description='Configuration panel for Wacom devices')

	help_loglevel = 'one of: \'debug, info, warning, error, fatal\' (more to less verbosity)'
	help_debug    = 'Enables \'debug\' loglevel. The same as -l debug'
	help_vendor   = 'Vendor code, hex value (eg 0x056a)'
	help_model    = 'Model code, hex value (eg 0x033e)'
	help_path     = 'Path to de device file under /dev (eg \'/dev/input/mouse0\')'
	help_database = 'LibWacom database path (eg \'/usr/share/libwacom\')'

	gr_loglevel = parser.add_mutually_exclusive_group()
	gr_loglevel.add_argument('-l', '--loglevel', dest='loglevel', choices=['debug', 'info', 'warning', 'error', 'fatal'], help=help_loglevel)
	gr_loglevel.add_argument('-d', '--debug',    dest='debug',    action='store_true', help=help_debug)

	parser.add_argument('-v', '--vendor', dest='device_vendor', required=False, default=0x056a, type=lambda x: int(x,0), help=help_vendor)

	gr_device = parser.add_mutually_exclusive_group()
	gr_device.add_argument('-m', '--model', dest='device_model', type=lambda x: int(x,0), help=help_model)
	gr_device.add_argument('-p', '--path',  dest='device_path',  type=lambda x: is_valid_device_file(parser, x), help=help_path)

	parser.add_argument('-b', '--database', dest='device_database', type=lambda x: is_valid_device_database(parser, x), help=help_database)

	return parser.parse_args()


class GSetWacom():

	MAIN_TAB_NOTABLET = 0
	MAIN_TAB_TABLET = 1

	def __init__(self, logger, args = None):
		self._logger = logger
		
		self._builder = Gtk.Builder()

		self._logger.debug("Creating DeviceRegisty")
		self._registry = DeviceRegistry()

		self._logger.debug("Creating DeviceBroker")
		if args and args.device_database:
			self._device_broker = DeviceBroker(args.device_database)
		else:
			self._device_broker = DeviceBroker()

		self._logger.debug("Creating DeviceScanner")
		self._scanner = DeviceScanner(self, self._registry, self._device_broker)

		if args and args.device_path:
			self._scanner.set_device_path(args.device_path)
		elif args and args.device_model:
			self._scanner.set_device_vendor_model(args.device_vendor, args.device_model)

		self._logger.debug("Creating main window")
		self._w_main = WMain(self)

	# Returns True if the application was successfully started.
	def run(self):
		try:
			self._logger.debug("Scanning devices...")
			self._scanner.scan()
			self._w_main.show()
			self._logger.debug("Launching scanner thread...") 
			self._scanner.start()
			Gtk.main()
			return True
		except GsException as ge:
			self._logger.fatal("Fatal Error:", ge)
			return False

	# This function is used to normally end the application.
	def quit(self):
		self._logger.info("Terminating the application...")
		Gtk.main_quit()

	# Retrieves a window from the Gtk builder and connect signals if signals_map is passed
	def get_window_from_file(self, file, name, signals_map = None):
		# TODO: check if the file has been added before
		self._builder.add_from_file(file)
		if not signals_map == None:
			self._builder.connect_signals(signals_map)
		return self._builder.get_object(name)	

	def get_logger(self):
		return self._logger

	def on_device_changes(self, running_devices, new_devices, deleted_devices):
		main_nb = self._builder.get_object("main_notebook")
		c_page  = main_nb.get_current_page()
		
		n_running = len(running_devices)
		n_new     = len(new_devices)
		n_deleted = len(deleted_devices)

		if n_deleted == 0 and n_new == 0:
			self._logger.debug("No changes")
			
		elif n_new > 0 and c_page == self.MAIN_TAB_NOTABLET:
			self._logger.info("%d new device(s) detected." % (n_new))
			main_nb.set_current_page(self.MAIN_TAB_TABLET)

		elif n_deleted > 0 and n_running == 0 and n_new == 0 and c_page == self.MAIN_TAB_TABLET:
			self._logger.info("All devices (%d) have been removed!" % (n_deleted))
			main_nb.set_current_page(self.MAIN_TAB_NOTABLET)

		elif n_deleted > 0 and (n_running > 0 or n_new > 0) and c_page == self.MAIN_TAB_TABLET:
			self._logger.warning("Some Wacom device has changed!")
			pass

		elif n_deleted == 0 and n_new > 0 and c_page == self.MAIN_TAB_TABLET:
			self._logger.warning("Some Wacom device has changed!")
			pass		


	# Any device change at the "libwacom" layer must be handled by this function
	# This will be triggered by the Scanner when it detects changes
	# These changes can be:
	# ~ new devices have been added
	# ~ some device has been removed
	def on_notify_device_changes(self, running_devices, new_devices, deleted_devices):
		#TODO: 
		# Check how we want to notify the user and handle the UI here.
		# Note that if this is called from the Scanner, then this call will run
		# in another thread different than Gtk.main 
		
		main_nb = self._builder.get_object("main_notebook")
		
		n_running = len(running_devices)
		n_new     = len(new_devices)
		n_deleted = len(deleted_devices)
		c_page    = main_nb.get_current_page()

		if n_deleted == 0 and n_new == 0:
			self._logger.debug("No changes")
			
		elif n_new > 0 and c_page == self.MAIN_TAB_NOTABLET:
			self._logger.info("Devices detected")
			main_nb.set_current_page(self.MAIN_TAB_TABLET)

		elif n_deleted > 0 and n_running == 0 and n_new == 0 and c_page == self.MAIN_TAB_TABLET:
			self._logger.info("All devices have been removed!")
			main_nb.set_current_page(self.MAIN_TAB_NOTABLET)

		elif n_deleted > 0 and (n_running > 0 or n_new > 0) and c_page == self.MAIN_TAB_TABLET:
			self._logger.warning("Some Wacom device has changed!")
			pass

		elif n_deleted == 0 and n_new > 0 and c_page == self.MAIN_TAB_TABLET:
			self._logger.warning("Some Wacom device has changed!")
			pass


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
