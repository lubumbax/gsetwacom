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

import glob

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
			device_p = self._lw.libwacom_new_from_path(self._db, 
			                                           path, 
			                                           WacomFallbackFlags.WFALLBACK_GENERIC, 
			                                           self._error)
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
				device_p = self._lw.libwacom_new_from_path(self._db, 
			                                               path, 
			                                               WacomFallbackFlags.WFALLBACK_NONE, 
			                                               self._error)
				if not device_p:
					#print "Scanning port " + path + ", nothing found"
					pass
				else:
					#print "Scanning port " + path + ", found: " + self._lw.libwacom_get_name(device_p)
					devices.append(self._create_device(device_p, path))
					#TODO: for now we only discover one device.
					# We have to study whether we want to handle more than 
					# one Wacom device in one system.
					break
		except LibWrapperException as lwe:
			raise GsError("Error while trying to find a device at %s" % (path), str(lwe))

		return devices

	def _create_device(self, device_p, path):
		# Minimum data that uniquely identifies a Device in the system.
		vendor = self._lw.libwacom_get_vendor_id(device_p)
		model = self._lw.libwacom_get_product_id(device_p)
		match = self._lw.libwacom_get_match(device_p)

		device = Device(self, path, vendor, model, match)

		device.set_class(self._lw.libwacom_get_class(device_p))
		device.set_name(self._lw.libwacom_get_name(device_p))
		device.set_layout_filename(self._lw.libwacom_get_layout_filename(device_p))
		device.set_width(self._lw.libwacom_get_width(device_p))
		device.set_height(self._lw.libwacom_get_height(device_p))
		device.set_has_stylus(self._lw.libwacom_has_stylus(device_p))
		device.set_has_touch(self._lw.libwacom_has_touch(device_p))
		device.set_num_buttons(self._lw.libwacom_get_num_buttons(device_p))
		device.set_match(self._lw.libwacom_get_match(device_p))
		
		device.set_has_ring(self._lw.libwacom_has_ring(device_p))
		device.set_has_ring2(self._lw.libwacom_has_ring2(device_p))
		device.set_has_touchswitch(self._lw.libwacom_has_touchswitch(device_p))
		device.set_ring_num_modes(self._lw.libwacom_get_ring_num_modes(device_p))
		device.set_ring2_num_modes(self._lw.libwacom_get_ring2_num_modes(device_p))
		device.set_num_strips(self._lw.libwacom_get_num_strips(device_p))
		device.set_strips_num_modes(self._lw.libwacom_get_strips_num_modes(device_p))

		#n_styli = c_int(0)
		#styli = _lw.libwacom_get_supported_styli(_device, byref(n_styli))
		#print "Num Styli:", n_styli.value
		#for n in range(n_styli.value):
		#	stylus_p = _lw.libwacom_stylus_get_for_id(_db, styli[n])
		#	stylus_name = _lw.libwacom_stylus_get_name(stylus_p)
		#	stylus_nbutt = _lw.libwacom_stylus_get_num_buttons(stylus_p)
		#	stylus_haser = _lw.libwacom_stylus_has_eraser(stylus_p)
		#	stylus_isera = _lw.libwacom_stylus_is_eraser(stylus_p)
		#	stylus_hasln = _lw.libwacom_stylus_has_lens(stylus_p)
		#	stylus_haswh = _lw.libwacom_stylus_has_wheel(stylus_p)
		#	stylus_axes = _lw.libwacom_stylus_get_axes(stylus_p)
		#	stylus_type = _lw.libwacom_stylus_get_type(stylus_p)
		#	stylus_data = (n, styli[n], stylus_name, stylus_nbutt, stylus_haser, stylus_isera, stylus_hasln, stylus_haswh, stylus_axes, stylus_type)
		#	print "- Stylus %d: %d - %s (Num. Buttons: %d, Has Eraser: %s, Is Eraser: %s, Has Lens: %s, Has Wheel: %s, Axes: %s, Type: %s)" % stylus_data
		#	#_lw.libwacom_print_stylus_description(1, stylus_p)

		#n_leds = c_int(0)
		#leds = _lw.libwacom_get_status_leds(_device, byref(n_leds))
		#print "Num. Status LEDs:", n_leds.value
		#for n in range(n_leds.value):
		#	print "Status LED %d: %d" % (n, leds[n])

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

	# FIXME: Return some sort of string that allows us to identify the device 
	# uniquely on the system where it is (or was) running. 
	# So far we will use "path:vendor:model" but it has to change.
	# What happens if we have a "Wacom Intuos XYZ" detected by 
	# "/dev/input/mouse3" and this device uses more than one path like "mouse4"
	#  and "mouse6"? The scanner would discover one more "Wacom Intuos XYZ" by 
	# "/dev/input/mouse4" and "/dev/input/mouse6".
	# Other possibility is that the device is unplugged and then plugged again,
	# maybe on another port. This has to be still the same device.
	# On each case, the application might want to keep a registry of what was
	# present in the system before it was removed. If a device comes back to
	# life the settings introduced by the user can thus be preserved.
	# There must be another way to grant unicity, so what we discover by
	# "/dev/input/mouse3" is exactly the same as what we discover by 
	# "/dev/input/mouse4". Maybe some sort of internal Id. Whatever it is, that
	# is what we have to pass to the constructor of Device.
	def get_id(self):
		#return "%s:%s:%s" % (self._path, self._vendor, self._model)
		# Testing with just 'vendor' and 'model'
		return "%s:%s" % (self._vendor, self._model)

	# Data from LibWacom

	def set_class(self, klass):
		self._class = klass

	def get_class(self):
		return self._class

	def set_name(self, name):
		self._name = name

	def get_name(self):
		return self._name

	def set_layout_filename(self, layout_filename):
		self._layout_filename = layout_filename

	def get_layout_filename(self):
		return self._layout_filename

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

	def has_stylus(self):
		return self._has_stylus

	def set_has_touch(self, has_touch = True):
		self._has_touch = bool(has_touch)

	def has_touch(self):
		return self._has_touch

	def set_num_buttons(self, num_buttons):
		self._num_buttons = num_buttons

	def get_num_buttons(self):
		return self._num_buttons

	def set_match(self, match):
		self._match = match

	def get_match(self):
		return self._match


	def set_has_ring(self, has_ring = True):
		self._has_ring = bool(has_ring)

	def has_ring(self):
		return self._has_ring

	def set_has_ring2(self, has_ring2 = True):
		self._has_ring2 = bool(has_ring2)

	def has_ring2(self):
		return self._has_ring2

	def set_has_touchswitch(self, has_touchswitch = True):
		self._has_touchswitch = bool(has_touchswitch)

	def has_touchswitch(self):
		return self._has_touchswitch

	def set_ring_num_modes(self, ring_num_modes):
		self._ring_num_modes = ring_num_modes

	def get_ring_num_modes(self):
		return self._ring_num_modes

	def set_ring2_num_modes(self, ring2_num_modes):
		self._ring2_num_modes = ring2_num_modes

	def get_ring2_num_modes(self):
		return self._ring2_num_modes

	def set_num_strips(self, num_strips):
		self._num_strips = num_strips

	def get_num_strips(self):
		return self._num_strips

	def set_strips_num_modes(self, strips_num_modes):
		self._strips_num_modes = strips_num_modes

	def get_strips_num_modes(self):
		return self._strips_num_modes


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

class Stylus():

	def __init__(self):
		pass

	def set_has_eraser(self, has_eraser = True):
		self._has_eraser = bool(has_eraser)

	def has_eraser(self):
		return self._has_eraser

	def set_is_eraser(self, is_eraser = True):
		self._is_eraser = bool(is_eraser)

	def is_eraser(self):
		return self._is_eraser

	def set_has_lens(self, has_lens = True):
		self._has_lens = bool(has_lens)

	def has_lens(self):
		return self._has_lens


