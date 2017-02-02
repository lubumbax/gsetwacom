# -*- Mode: Python; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*- #
# device.py
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

from error import GsException, GsError

from libwacom import LibWacom, LibWrapperException, WacomFallbackFlags, WacomDevice
from ctypes import byref

class DeviceBroker():

	'''
	Interface with LibWacom and other libraries to retrieve information about 
	the device and set get/set its properties.

	This class does not send information to Logger(). It just returns a 
	GsError (extends GsException) to notify of error situations. It is up to
	the application to report them down to the logs or not. 

	DeviceBroker instantiates a full WacomDatabase which retrieves... [TODO]

	[TODO]: a whole lot of work has yet to be done here. We still have to 
	translate wacom-properties.h, wacom-util.h and Xwacom.h, and then implement
	xsetwacom.c, all from the "xf86-input-wacom" project.
	'''

	def __init__(self, database = None):

		self._lw = LibWacom()
		self._db = None
		self._error = None

		try:
			self._error = self._lw.libwacom_error_new()
			if database is None:
				self._db = self._lw.libwacom_database_new()
			else:
				self._db = self._lw.libwacom_database_new_for_path(database)
		except LibWrapperException as lwe:
			raise GsError("Couldn't create a Scanner.", str(lwe))

	def __del__(self):

		# TODO: check what has happened with any device created by LibWacom. 
		# We need to make sure that they are uninitialized. 
		if bool(self._db):
			self._lw.libwacom_database_destroy(self._db)
		if bool(self._error):
			self._lw.libwacom_error_free(byref(self._error))

	# TODO: free any device_p created in here
	def find_by_path(self, path):
		try:
			device_p = self._lw.libwacom_new_from_path(self._db, path, WacomFallbackFlags.WFALLBACK_GENERIC, self._error)
			if not bool(device_p):
				return None
			else:
				return self._create_device(device_p, path)
		except LibWrapperException as lwe:
			raise GsError("Error while trying to find a device at %s" % (path), str(lwe))

	# TODO: free any device_p created in here
	def find_by_usbid(self, vendor, model):
		try:		
			error = self._lw.libwacom_error_new()
			device_p = self._lw.libwacom_new_from_usbid(self._db, vendor, model, self._error)
			if not bool(device_p):
				return None
			else:
				return self._create_device(device_p, "/dev/null")       # TODO: find path
		except LibWrapperException as lwe:
			raise GsError("Error while trying to find a device at %s:%s" % (hex(vendor), hex(model)), str(lwe))

	# probe each /dev/input/mouse* and see which one is a Wacom device. 
	# TODO: free any device_p created in here
	def find_all(self):
		path = ""
		devices = []
		try:
			for path in glob.glob('/dev/input/mouse*'):
				device_p = self._lw.libwacom_new_from_path(self._db, path, WacomFallbackFlags.WFALLBACK_NONE, self._error)
				if bool(device_p):
					devices.append(self._create_device(device_p, path))
		except LibWrapperException as lwe:
			raise GsError("Error while trying to find a device at %s" % (path), str(lwe))

	def _create_device(self, device_p, path):
		# Minimum data that uniquely identifies a Device in the system.
		vendor = self._lw.libwacom_get_vendor_id(device_p)
		model = self._lw.libwacom_get_product_id(device_p)
		match = self._lw.libwacom_get_match(device_p)

		device = Device(self, path, vendor, model, match)

		device.set_name(self._lw.libwacom_get_name(device_p))
		device.set_width(self._lw.libwacom_get_width(device_p))
		device.set_height(self._lw.libwacom_get_height(device_p))
		device.set_has_stylus(self._lw.libwacom_has_stylus(device_p))
		device.set_has_touch(self._lw.libwacom_has_touch(device_p))
		device.set_num_buttons(self._lw.libwacom_get_num_buttons(device_p))
		
		return device

# TODO: maybe better called DeviceSet as it would wrap a "set" of devices like
# a tablet, pen, eraser and touch.
class Device():

	GENERIC_NAME = "Generic Wacom"

	'''
	This class holds "passive" data of a Wacom Device, ie, it doesn't access 
	LibWacom or any other Ctypes wrapper. 
	All Ctypes level data has to be retrieved/set via DeviceSomething class (TODO)
	'''

	# path, vendor and model are the minimum mandatory properties that have to
	# be set to a Device. 
	def __init__(self, broker, path, vendor, model, match):
		self._broker = broker
		self._path = path
		self._vendor = vendor
		self._model = model
		self._match = match

		self._name = self.GENERIC_NAME

	# TODO: Return some sort of string that allows us to identify the device 
	# uniquely on the system where it is (or was) running. 
	# So far we will use "path:vendor:model".
	# But I am not so sure that it is enough. What happens if we have a
	# "Wacom Intuos XYZ" detected by "/dev/input/mouse3" and this device uses
	# more than one path like "mouse4" and "mouse6"? The scanner would discover
	# one more "Wacom Intuos XYZ" by "/dev/input/mouse4" and "/dev/input/mouse6".
	# There must be another way to grant unicity, so what we discover by
	# "/dev/input/mouse3" is exactly the same as what we discover by 
	# "/dev/input/mouse4". Maybe some sort of internal Id. Whatever it is, that
	# is what we have to pass to the constructor of Device.
	def get_id(self):
		return "%s:%s:%s" % (self._path, self._vendor, self._model)

	def set_name(self, name):
		self._name = name

	def get_name(self):
		return self._name

	def set_width(self, width):
		self._width = width

	def get_width(self):
		return self._width

	def set_height(self, height):
		self._height = height

	def get_height(self):
		return self._height

	def set_has_stylus(self, has_stylus = True):
		self._has_stylus = bool(has_stylus)

	def get_has_stylus(self):
		return self._has_stylus

	def set_has_touch(self, has_touch = True):
		self._has_touch = bool(has_touch)

	def get_has_touch(self):
		return self._has_touch

	def set_num_buttons(self, num_buttons):
		self._num_buttons = num_buttons

	def get_num_buttons(self):
		return self._num_buttons

	# Checks if "device" is exactly the same as the current one. 
	# For that, not only the id but also other characteristics are checked
	# like, for example the device has now one more pen, or an airbrush is gone
	# Returns True if they exactly the same
	def is_full_match(self, device):
		# For now we assume that they are exactly the same if they just match 
		# 'id' and a few other properties.
		if self.get_id() != device.get_id():
			return False
		if self.get_name() != device.get_name():
			return False
		if self.get_height() != device.get_height():
			return False
		if self.get_width() != device.get_width():
			return False

		return True

	'''
	TODO: 
	Add a Device cache data refresher thread per Device. 
	That thread will check properties from the Device from time to time and 
	compare to the currently stored ones in the Device object. If there is a 
	difference the property is marked "dirty". 
	This is to have the application know that something (xsetwacom?) can have 
	externally configured the device so we might want to refresh the UI with 
	the new values. The thread could use a PropertyChanged exception. This is
	to be determined yet.
	'''
