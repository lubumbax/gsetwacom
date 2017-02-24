# -*- Mode: Python; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*- #
# scanner.py
# Copyright (C) 2017 Juan Carlos Muro <murojc@gmail.com>
#
# gsetwacom is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# gsetwacom is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess
import re
import glob

from threading import Thread
from time      import sleep

from ctypes import byref
from libwrapper import LibWrapperException

from error import GsError


class DeviceScanner():

	def __init__(self, app, registry, broker):
		self._app = app
		self._logger = app.get_logger()  # TODO: check that logger is not null, otherwise rise a custom InitException or so
		self._keep_scanning = False
		self._registry = registry        # Registry()
		self._period = 1                 # seconds
		self._iterations = 0             # Keeps track of times the scanner scanned

		self._device_path = None         # If this is specified, try to find a Wacom device there
		self._device_vendor = None       # If vendor and model are specified,
		self._device_model = None        # try to find a Wacom device there
		#self._device_simulation = False    # In simulation mode we simulate the Wacom device by 'vendor:model'

		self._broker = broker
		#self._lw = LibWacom()  # TODO: these two will not be used here but in interface classes (DeviceFinder, ...)
		#self._db = None        # TODO: check the app argument 'args.device_database' and create the database based on that

		try:
			#self._db = self._lw.libwacom_database_new()
			pass
		except LibWrapperException as lwe:
			raise GsError("Couldn't create a Scanner", lwe)

		#self._error = self._lw.libwacom_error_new()
		#self._device = None

	def __del__(self):
		##if self._device != None and self._device:  
		##	self._lw.libwacom_destroy(self._device)
		#self._lw.libwacom_database_destroy(self._db)
		##self._lw.libwacom_error_free(c_void_p(self._error))
		pass

	# Sets the device path under /dev
	# Once this is set, the scanner will not use in "autodetect mode"
	# TODO: make this atomic so that it doesn't conflict with the scan thread
	def set_device_path(self, path):
		self._device_path = path
		self._device_vendor = None
		self._device_model = None

	# Sets the device vendor and model for the scanner.
	# Once this is set, the scanner will not use in "autodetect mode"
	# TODO: make this atomic so that it doesn't conflict with the scan thread
	def set_device_vendor_model(self, vendor, model):
		self._device_path = None
		self._device_vendor = vendor
		self._device_model = model

	# Sets the scanner to simulation mode. 
	# In simulation_mode the scanner tries to simulate the device by vendor:model.
	# simulation_mode won't be set if there is no vendor:model
	# TODO: make this atomic so that it doesn't conflict with the scan thread
	#def set_device_simulation(self, simulation_mode = False):
	#	if _device_simulation and not (self._device_vendor and self._device_model):
	#		return
	#	self._device_simulation = simulation_mode

	# Indicates if we have to attach to a device path / vendor:model or rather 
	# we try to scan /dev/input/mouse*
	#def is_auto_discovery():
	#	# this condition shouldn't happen, but if there is a path then we don't
	#	# auto-discovery
	#	if self._device_path and self._device_simulation:
	#		return False
	#	elif self._device_path and not self._device_simulation:
	#		return True
	#	elif not self._device_path:
	#		if self._device_simulation and (self._device_vendor and self._device_model):
	#			return 
	#		else:
			

	def start(self):
		# Start thread and loop 
		thread = Thread(target = self._run)
		thread.daemon = True
		thread.start()
		#self.thread.join()

	# This function is called in a thread. Runs the scan process.
	def _run(self):
		self._keep_scanning = True
		while self._keep_scanning:
			sleep(self._period)
			self._logger.debug("Scanning...")
			self.scan()
		self._logger.debug("Scanner thread finished!")

	# Returns a list of available device paths
	#def find_wacom_device_path(self):
	#	# TODO: return the actual devices
	#	return DEVICE_PATH[0]

	# Run less frequently after the first 3 iterations @1 sec. 
	# TODO: implement algorighm to calculate the period 
	def _get_scan_period(self):
		return 5

	# Checks available devices from the OS and updates the registry.
	# Then it notifies the application with changes.
	def scan(self):
		#if self._iterations < 3:
		#	self._iterations = self._iterations + 1
		#	return False
			
		self._period = self._get_scan_period()  # Run less frequently after the first 3 iterations @1 sec. 

		'''
		-p /dev/input/mouse0  => Try to find device. If found ~> handle that device and don't discover others (the device can be randomly plugged / unplugged)
		-v vendor -m model    => Simulate a device by vendor:model. Don't try to discover anything.
		<nothing>             => Try to discover any Wacom device detected (randomly plugged / unplugged)
		'''

		try:
			self._registry.begin()    # TODO: wrap try/except for GsRegistryException's

			# find by path
			if self._device_path:
				self._logger.info("Finding device at " + self._device_path)
				device = self._broker.find_by_path(self._device_path)                        # TODO: free internal LibWacom devices later, somehow
				if device is None:
					self._logger.info("Device not found at" + self._device_path)
					return False
				self._registry.register(device)
				
			# simulate vendor:model
			elif self._device_model:
				self._logger.info("Simulating " + hex(self._device_vendor) + ":" + hex(self._device_model))
				device = self._broker.find_by_usbid(self._device_vendor, self._device_model)            # TODO: free internal LibWacom devices later
				if device is None:
					self._logger.warning("Can't simulate a device by vendor " + hex(self._device_vendor) + " and model " + hex(self._device_model))
					return False
				self._registry.register(device)

			# discover
			else:
				self._logger.info("Discovering connected devices")
				devices = self._broker.find_all()                                                        # TODO: free internal LibWacom devices later
				for device in devices:
					self._registry.register(device)

			self._registry.end_checking()

		except LibWrapperException as lwe:
			self._logger.error(str(lwe))
			return False
		
		devices_running = self._registry.get_devices_running()
		devices_new = self._registry.get_devices_new()
		devices_deleted = self._registry.get_devices_deleted()
		self._app.on_device_changes(devices_running, devices_new, devices_deleted)

		self._registry.commit()
		return True
		
		
		##output = subprocess.check_output(["lsusb"]).splitlines()
		##output = subprocess.check_output(["xsetwacom", "--list", "devices"]).splitlines()
		#output = subprocess.check_output(["xsetwacom.sh", "--list", "devices"]).splitlines()
		#for line in output:
		#	self._logger.info("> " + line)
		#
		## Filter the output of xsetwacom returning an arrary of dictionaries.
		## Each dictionary corresponds to a device and contains three elements:
		## "id", "name" and "type".
		#regex = re.compile("(.*)id:\s*(\d+)\s*type\:\s*(.*)")
		#devices = [{ 'name': m.group(1).strip(), 
		#             'id': m.group(2), 
		#			 'type': m.group(3).strip() } for line in output for m in [regex.search(line)] if m]
		#
		#device_names = [dev['name'] for dev in devices if 'name' in dev]
		#device_set_name = get_device_set_name_from_list(device_names)
		#self._logger.debug("Device Set Name: " + device_set_name)
		#
		#for device in devices:
		#	self._registry.set_devices_status_checking()              # TODO: rename to start_checking()
		#	self._registry.register_device(device_set_name, device['id'], device['name'], device['type'])	
		#
		## Devices still in STATUS_CHECKING have to be removed (not in the list)
		#self._registry.remove_devices_on_checking(device_set_name)    # TODO: rename to stop_checking()
		#
		## Now we need to notify the app
		## If devices in STATUS_NEW or STATUS_DELETED we need to notify the UI
		## If devices in STATUS_NEW
		#self._app.on_notify_device_changes(self._registry.get_devices_running_from_set(device_set_name),
		#                                   self._registry.get_devices_new_from_set(device_set_name),
		#                                   self._registry.get_devices_deleted_from_set(device_set_name))


		





# Given a list of strings, returns the longest common leading component
def get_device_set_name_from_list(list):
	if not list: return ''
	a, b = min(list), max(list)
	lo, hi = 0, min(len(a), len(b))
	while lo < hi:
		mid = (lo+hi)//2 + 1
		if a[lo:mid] == b[lo:mid]:
			lo = mid
		else:
			hi = mid - 1
	return a[:hi]


