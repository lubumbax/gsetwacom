# -*- Mode: Python; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*- #
# libwacom.py
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

'''
Wrapper for libwacom.h from 
http://linuxwacom.sourceforge.net/wiki/index.php/Libwacom

This code is based on LibraryWrapper from "base.py" from the Evemu project at
https://www.freedesktop.org/wiki/Evemu/
'''

import ctypes
import ctypes.util
import os
import sys

from libwrapper import *

# TODO: find what types are being used and what not
from ctypes import c_char, c_char_p, c_int, c_uint, c_void_p, c_long, c_ulong, c_int32, c_uint32, c_uint16, c_bool, POINTER, Structure


class WacomErrorCode:   # Possible error codes
	'''
	enum WacomErrorCode {
		WERROR_NONE,
		WERROR_BAD_ALLOC,
		WERROR_INVALID_PATH,
		WERROR_INVALID_DB,
		WERROR_BAD_ACCESS,
		WERROR_UNKNOWN_MODEL,
	};
	'''
	WERROR_NONE          = 0   # No error has occured
	WERROR_BAD_ALLOC     = 1   # Allocation error
	WERROR_INVALID_PATH  = 2   # A path specified is invalid
	WERROR_INVALID_DB    = 3   # The passed DB is invalid
	WERROR_BAD_ACCESS    = 4   # Invalid permissions to access the path
	WERROR_UNKNOWN_MODEL = 5   # Unsupported/unknown device


class WacomBusType:     # Bus types for tablets.
	'''
	typedef enum {
		WBUSTYPE_UNKNOWN,
		WBUSTYPE_USB,
		WBUSTYPE_SERIAL,
		WBUSTYPE_BLUETOOTH,
		WBUSTYPE_I2C,
	} WacomBusType;
	'''
	WBUSTYPE_UNKNOWN   = 0   # Unknown/unsupported bus type
	WBUSTYPE_USB       = 1   # USB tablet
	WBUSTYPE_SERIAL    = 2   # Serial tablet
	WBUSTYPE_BLUETOOTH = 3   # Bluetooth tablet
	WBUSTYPE_I2C       = 4   # I2C tablet


class WacomIntegrationFlags:     # Tablet integration.
	'''
	typedef enum {
		WACOM_DEVICE_INTEGRATED_NONE    = 0,
		WACOM_DEVICE_INTEGRATED_DISPLAY = (1 << 0),
		WACOM_DEVICE_INTEGRATED_SYSTEM  = (1 << 1)
	} WacomIntegrationFlags;
	'''
	WACOM_DEVICE_INTEGRATED_NONE    = 0
	WACOM_DEVICE_INTEGRATED_DISPLAY = 1 << 0
	WACOM_DEVICE_INTEGRATED_SYSTEM  = 1 << 1


class WacomClass:     # Classes of devices
	'''
	typedef enum {
		WCLASS_UNKNOWN,
		WCLASS_INTUOS3,
		WCLASS_INTUOS4,
		WCLASS_INTUOS5,
		WCLASS_CINTIQ,
		WCLASS_BAMBOO,
		WCLASS_GRAPHIRE,
		WCLASS_ISDV4,
		WCLASS_INTUOS,
		WCLASS_INTUOS2,
		WCLASS_PEN_DISPLAYS,
		WCLASS_REMOTE,
	} WacomClass;
	'''
	WCLASS_UNKNOWN       = 0    # Unknown/unsupported device class
	WCLASS_INTUOS3       = 1    # Any Intuos3 series
	WCLASS_INTUOS4       = 2    # Any Intuos4 series
	WCLASS_INTUOS5       = 3    # Any Intuos5 series
	WCLASS_CINTIQ        = 4    # Any Cintiq device
	WCLASS_BAMBOO        = 5    # Any Bamboo device
	WCLASS_GRAPHIRE      = 6    # Any Graphire device
	WCLASS_ISDV4         = 7    # Any serial ISDV4 device
	WCLASS_INTUOS        = 8    # Any Intuos series
	WCLASS_INTUOS2       = 9    # Any Intuos2 series
	WCLASS_PEN_DISPLAYS  = 10   # Any "interactive pen display"
	WCLASS_REMOTE        = 11   # Any Wacom Remote


class WacomStylusType:      # Class of stylus
	'''
	typedef enum {
		WSTYLUS_UNKNOWN,
		WSTYLUS_GENERAL,
		WSTYLUS_INKING,
		WSTYLUS_AIRBRUSH,
		WSTYLUS_CLASSIC,
		WSTYLUS_MARKER,
		WSTYLUS_STROKE,
		WSTYLUS_PUCK
	} WacomStylusType;
	'''
	WSTYLUS_UNKNOWN  = 0
	WSTYLUS_GENERAL  = 1
	WSTYLUS_INKING   = 2
	WSTYLUS_AIRBRUSH = 3
	WSTYLUS_CLASSIC  = 4
	WSTYLUS_MARKER   = 5
	WSTYLUS_STROKE   = 6
	WSTYLUS_PUCK     = 7


class WacomButtonFlags:         # Capabilities of the various tablet buttons
	'''
	typedef enum {
		WACOM_BUTTON_NONE                   = 0,
		WACOM_BUTTON_POSITION_LEFT          = (1 << 1),
		WACOM_BUTTON_POSITION_RIGHT         = (1 << 2),
		WACOM_BUTTON_POSITION_TOP           = (1 << 3),
		WACOM_BUTTON_POSITION_BOTTOM        = (1 << 4),
		WACOM_BUTTON_RING_MODESWITCH        = (1 << 5),
		WACOM_BUTTON_RING2_MODESWITCH       = (1 << 6),
		WACOM_BUTTON_TOUCHSTRIP_MODESWITCH  = (1 << 7),
		WACOM_BUTTON_TOUCHSTRIP2_MODESWITCH = (1 << 8),
		WACOM_BUTTON_OLED                   = (1 << 9),
		WACOM_BUTTON_MODESWITCH             = (WACOM_BUTTON_RING_MODESWITCH | WACOM_BUTTON_RING2_MODESWITCH | WACOM_BUTTON_TOUCHSTRIP_MODESWITCH | WACOM_BUTTON_TOUCHSTRIP2_MODESWITCH),
		WACOM_BUTTON_DIRECTION              = (WACOM_BUTTON_POSITION_LEFT | WACOM_BUTTON_POSITION_RIGHT | WACOM_BUTTON_POSITION_TOP | WACOM_BUTTON_POSITION_BOTTOM),
		WACOM_BUTTON_RINGS_MODESWITCH       = (WACOM_BUTTON_RING_MODESWITCH | WACOM_BUTTON_RING2_MODESWITCH),
		WACOM_BUTTON_TOUCHSTRIPS_MODESWITCH = (WACOM_BUTTON_TOUCHSTRIP_MODESWITCH | WACOM_BUTTON_TOUCHSTRIP2_MODESWITCH),
	} WacomButtonFlags;
	'''
	WACOM_BUTTON_NONE                   = 0
	WACOM_BUTTON_POSITION_LEFT          = 1 << 1
	WACOM_BUTTON_POSITION_RIGHT         = 1 << 2
	WACOM_BUTTON_POSITION_TOP           = 1 << 3
	WACOM_BUTTON_POSITION_BOTTOM        = 1 << 4
	WACOM_BUTTON_RING_MODESWITCH        = 1 << 5
	WACOM_BUTTON_RING2_MODESWITCH       = 1 << 6
	WACOM_BUTTON_TOUCHSTRIP_MODESWITCH  = 1 << 7
	WACOM_BUTTON_TOUCHSTRIP2_MODESWITCH = 1 << 8
	WACOM_BUTTON_OLED                   = 1 << 9
	WACOM_BUTTON_MODESWITCH             = WACOM_BUTTON_RING_MODESWITCH | WACOM_BUTTON_RING2_MODESWITCH | WACOM_BUTTON_TOUCHSTRIP_MODESWITCH | WACOM_BUTTON_TOUCHSTRIP2_MODESWITCH
	WACOM_BUTTON_DIRECTION              = WACOM_BUTTON_POSITION_LEFT | WACOM_BUTTON_POSITION_RIGHT | WACOM_BUTTON_POSITION_TOP | WACOM_BUTTON_POSITION_BOTTOM
	WACOM_BUTTON_RINGS_MODESWITCH       = WACOM_BUTTON_RING_MODESWITCH | WACOM_BUTTON_RING2_MODESWITCH
	WACOM_BUTTON_TOUCHSTRIPS_MODESWITCH = WACOM_BUTTON_TOUCHSTRIP_MODESWITCH | WACOM_BUTTON_TOUCHSTRIP2_MODESWITCH

class WacomAxisTypeFlags:  # Axis type for a stylus. Note that x/y is implied.
	'''
	typedef enum {
		WACOM_AXIS_TYPE_NONE                = 0,
		/** Tilt in x and y direction */
		WACOM_AXIS_TYPE_TILT                = (1 << 1),
		/** Rotation in the z-axis */
		WACOM_AXIS_TYPE_ROTATION_Z          = (1 << 2),
		/** Distance to surface */
		WACOM_AXIS_TYPE_DISTANCE            = (1 << 3),
		/** Tip pressure */
		WACOM_AXIS_TYPE_PRESSURE            = (1 << 4),
		/** A absolute-position slider like the wheel on the airbrush */
		WACOM_AXIS_TYPE_SLIDER              = (1 << 5),
	} WacomAxisTypeFlags;
	'''
	WACOM_AXIS_TYPE_NONE       = 0
	WACOM_AXIS_TYPE_TILT       = 1 << 1    # Tilt in x and y direction
	WACOM_AXIS_TYPE_ROTATION_Z = 1 << 2    # Rotation in the z-axis
	WACOM_AXIS_TYPE_DISTANCE   = 1 << 3    # Distance to surface
	WACOM_AXIS_TYPE_PRESSURE   = 1 << 4    # Tip pressure
	WACOM_AXIS_TYPE_SLIDER     = 1 << 5    # A absolute-position slider like the wheel on the airbrush


class WacomFallbackFlags:
	'''
	typedef enum {
		WFALLBACK_NONE = 0,
		WFALLBACK_GENERIC = 1
	} WacomFallbackFlags;
	'''
	WFALLBACK_NONE    = 0
	WFALLBACK_GENERIC = 1


class WacomCompareFlags:
	'''
	typedef enum {
		WCOMPARE_NORMAL		= 0,
		WCOMPARE_MATCHES	= (1 << 1),
	} WacomCompareFlags;
	'''
	WCOMPARE_NORMAL  = 0         # compare the device only
	WCOMPARE_MATCHES = 1 << 1    # compare all possible matches too


class WacomStatusLEDs:
	'''
	typedef enum {
		WACOM_STATUS_LED_UNAVAILABLE	= -1,
		WACOM_STATUS_LED_RING		= 0,
		WACOM_STATUS_LED_RING2		= 1,
		WACOM_STATUS_LED_TOUCHSTRIP	= 2,
		WACOM_STATUS_LED_TOUCHSTRIP2	= 3
	} WacomStatusLEDs;
	'''
	WACOM_STATUS_LED_UNAVAILABLE = -1
	WACOM_STATUS_LED_RING        = 0
	WACOM_STATUS_LED_RING2       = 1
	WACOM_STATUS_LED_TOUCHSTRIP  = 2
	WACOM_STATUS_LED_TOUCHSTRIP2 = 3



class WacomFeature:
	'''
	enum WacomFeature {
		FEATURE_STYLUS		= (1 << 0),
		FEATURE_TOUCH		= (1 << 1),
		FEATURE_RING		= (1 << 2),
		FEATURE_RING2		= (1 << 3),
		FEATURE_REVERSIBLE	= (1 << 4),
		FEATURE_TOUCHSWITCH	= (1 << 5)
	};
	'''
	FEATURE_STYLUS      = 1 << 0
	FEATURE_TOUCH       = 1 << 1
	FEATURE_RING        = 1 << 2
	FEATURE_RING2       = 1 << 3
	FEATURE_REVERSIBLE  = 1 << 4
	FEATURE_TOUCHSWITCH = 1 << 5


class WacomMatch(Structure):
	'''
	struct _WacomMatch {
		char *match;
		char *name;
		WacomBusType bus;
		uint32_t vendor_id;
		uint32_t product_id;
	};
	'''
	_fields_ = [
	    ("match", c_char_p),
	    ("name", c_char_p),
	    ("bus", c_int),             # enum WacomBusType
	    ("vendor_id", c_uint32),    # uint32_t
	    ("product_id", c_uint32)    # uint32_t
	]


class WacomDevice(Structure):
	'''
	struct _WacomDevice {
		char *name;
		int width;
		int height;

		int match;	/* used match or first match by default */
		WacomMatch **matches; /* NULL-terminated */
		int nmatches; /* not counting NULL-terminated element */

		WacomMatch *paired;

		WacomClass cls;
		int num_strips;
		uint32_t features;
		uint32_t integration_flags;

		int strips_num_modes;
		int ring_num_modes;
		int ring2_num_modes;

		gsize num_styli;
		int *supported_styli;

		int num_buttons;
		WacomButtonFlags *buttons;

		int num_leds;
		WacomStatusLEDs *status_leds;

		char *layout;

		gint refcnt; /* for the db hashtable */
	};
	'''
	_fields_ = [
	    ("name", c_char_p),
	    ("width", c_int),
	    ("height", c_int),

	    ("match", c_char_p),
	    ("matches", POINTER(POINTER(WacomMatch))),  # struct _WacomMatch **
	    ("nmatches", c_int),

	    ("paired", POINTER(WacomMatch)),            # struct _WacomMatch *

	    ("cls", c_int),                             # enum WacomClass
	    ("num_strips", c_int),
	    ("features", c_uint32),                     # uint32_t
	    ("integration_flags", c_uint32),            # uint32_t

	    ("strips_num_modes", c_int),
	    ("ring_num_modes", c_int),
	    ("ring2_num_modes", c_int),

	    ("num_styli", c_ulong),                     # gsize
	    ("supported_styli", POINTER(c_int)),        # int *

	    ("num_buttons", c_int),
	    ("buttons", c_void_p),                      # enum WacomButtonFlags *

	    ("num_leds", c_int),
	    ("status_leds", c_void_p),                  # enum WacomStatusLEDs *

	    ("layout", c_char_p),

	    ("refcnt", c_int)
	]


class WacomStylus(Structure):
	'''
	struct _WacomStylus {
		int id;
		char *name;
		int num_buttons;
		gboolean has_eraser;
		gboolean is_eraser;
		gboolean has_lens;
		gboolean has_wheel;
		WacomStylusType type;
		WacomAxisTypeFlags axes;
	};
	'''
	_fields_ = [
	    ("id", c_int),
	    ("name", c_char_p),
		("num_buttons", c_int),
		("has_eraser", c_bool),
		("is_eraser", c_bool),
		("has_lens", c_bool),
		("has_wheel", c_bool),
		("type", c_int),            # enum WacomStylusType
		("axes", c_int)             # enum WacomAxisTypeFlags
	]


class WacomError(Structure):
	'''
	struct _WacomError {
		enum WacomErrorCode code;
		char *msg;
	};
	'''
	_fields_ = [
	    ("code", c_int),            # enum WacomErrorCode
	    ("msg", c_char_p)
	]


def ctypes_errcheck(result, func, args, skip_errors = []):
	errno = ctypes.get_errno()
	if errno != 0:
		errno_str = "(Ctypes error %d) - %s" % (errno, os.strerror(errno))
		raise LibWacomError(errno_str, result, func, args)
	else:
		return result

# TODO: 
# We are using for "errockeck" the previous "ctypes_errcheck" or any of the callers of this "libwacom_errcheck".
# Add a check for ctypes errors here as well. 
def libwacom_errcheck(result, func, args, skip_errors = []):

	'''
	Finds a "WacomError *" argument in the prototype of "func" and in case the
	error is other than WERROR_NONE or any of the specified in "skip_errors" it
	raises a LibWacomError.

	In case the error is one of WERROR_NONE or any of the specified in 
	"skip_errors", it results in no exception and just returns "result".

	In case a "WacomError *" argument is not found in the prototype of "func", 
	it results in no exception and just returns "result".
	
	This error checker returns "None" in case the return value of "func" is NULL 
	and the error object contains WERROR_NONE or "WERROR_UNKNOWN_MODEL".
	Otherwise a LibWacomError is risen.
	This is intented to be used with functions like "libwacom_new_from_path" or
	"libwacom_new_from_usbid".
	Use this error checker only with C prototypes that have a "WacomError *" 
	argument.
	'''

	_error = None

	if not WacomErrorCode.WERROR_NONE in skip_errors:
		skip_errors.append(WacomErrorCode.WERROR_NONE)

	# Search a "WacomError *" in the parameters list
	for (num, argtype) in enumerate(func.argtypes):
		#if argtype == POINTER(WacomError) and args[num] is True:
		#if argtype == POINTER(WacomError):
		if argtype == POINTER(WacomError) and args[num]:
			#print "*****", argtype.__name__, args[num]
			_error = args[num].contents
			break

	if _error is None:
		#print "[libwacom.libwacom_errcheck()]:", "Error argument not found in prototype"
		return result

	#if result or _error.code in skip_errors:
	#	#print "[libwacom.libwacom_errcheck()]:", "No error"
	#	return result
	#else:
	#	raise LibWacomError(_error, result, func, args)

	#print skip_errors

	#print "[libwacom.libwacom_errcheck()]: Type of _error:", type(_error)
	#print "[libwacom.libwacom_errcheck()]: _error.code:", _error.code
	if not _error.code in skip_errors:
		#print "[libwacom.libwacom_errcheck()]:", "Raising exception"
		raise LibWacomError(_error, result, func, args)

		#raise LibWacomError(_error)
		#raise LibWacomError(_error, result, func, args)
		#raise LibWacomError(None)
		#raise LibWacomError("something not a WacomError")
		#raise LibWacomError(_error, result)
		#raise LibWacomError(_error, result, func)
		#raise LibWacomError("something not a WacomError", result, func, args)
	else:
		#print "[libwacom.libwacom_errcheck()]:", "No error"
		return result


def libwacom_errcheck_skip_unknown(result, func, args):
	'''
	This error checker returns "None" in case the return value of "func" is NULL 
	and the error object contains WERROR_NONE or "WERROR_UNKNOWN_MODEL".
	Otherwise a LibWacomError is risen.
	This is intented to be used with functions like "libwacom_new_from_path" or
	"libwacom_new_from_usbid".
	Use this error checker only with C prototypes that have a "WacomError *" 
	argument.
	'''
	return libwacom_errcheck(result, func, args, skip_errors = [WacomErrorCode.WERROR_UNKNOWN_MODEL])
	#return libwacom_errcheck(result, func, args)

def libwacom_errcheck_skip_invalid_path(result, func, args):
	'''
	This error checker returns "None" in case the return value of "func" is NULL 
	and the error object contains WERROR_NONE or "WERROR_INVALID_PATH".
	Otherwise a LibWacomError is risen.
	This is intented to be used with functions like "libwacom_new_from_path" or
	"libwacom_new_from_usbid".
	Use this error checker only with C prototypes that have a "WacomError *" 
	argument.
	'''
	return libwacom_errcheck(result, func, args, skip_errors = [WacomErrorCode.WERROR_INVALID_PATH])
	#return libwacom_errcheck(result, func, args)


class LibWacomException(LibWrapperException):

	''' 
	LibWacomException is a base Exception for all Py LibWacom operations
	'''

	def __init__(self, message):
		super(LibWacomException, self).__init__(message)


class LibWacomError(LibWacomException):

	''' 
	LibWacomError is risen when any of the libwacom operations result in
	an error. 

	There will be cases in which a libwacom operation results in "something
	that we are expectign is not found". C libwacom internally returns the 
	"no result" situation as an error. Py Libwacom in these cases will not 
	result in a LibWacomException but rather in a None return value. 

	Usage:
		raise LibWacomError(_error)
		raise LibWacomError(_error, result, func, args)

	The following instances of LibWacomError are also possible, but not 
	recommended:
		raise LibWacomError(None)
		raise LibWacomError("something not a WacomError")
		raise LibWacomError(_error, result)
		raise LibWacomError(_error, result, func)
		raise LibWacomError("something not a WacomError", result, func, args)

	The reason is that LibWacomError is intented for C libwacom errors only.
	Other kind of error caused by Py LibWacom should be risen in a 
	LibWacomException or any subtype of it.
	'''

	# "error" is expected to be a WacomError object (not a pointer!)
	# In case you have a "WacomError *" pointer, make sure to pass 
	# "error_p.contents" to the constructor of LibWacomError
	def __init__(self, error, result = None, func = None, args = None):
		self._error_code = None
		self._error_msg  = ""
		self._call = None
		
		if (not error is None) and type(error).__name__ == 'WacomError':
			#print "[LibWacomError.__init__()]:", "Error passed is a WacomError: ", error.code, error.msg
			self._error_code = error.code
			if not error.msg is None: 
				self._error_msg  = error.msg
			else:
				# some libwacom functions don't set a message in case of 
				# WERROR_UNKNOWN_MODEL
				if error.code == WacomErrorCode.WERROR_UNKNOWN_MODEL:
					self._error_msg  = "Unknown Model"
		else:
			if not error is None:
				self._error_msg = repr(error)
			else: 
				#self._error_msg = ""
				#self._error_msg = " "
				self._error_msg  = "Reason Unknown"

		if not (result is None) and (not func is None) and (not args is None):
			self._call = self.get_call_str(result, func, args)

		if self._error_code is None:
			if self._call is None:
				#if len(self._error_msg) == 0:
				#	#message = "(No LibWacom error)"
				#	message = ""
				#else:
				#	#message = "(No LibWacom error)%s" % (self._error_msg,)
				#	message = "%s" % (self._error_msg,)
				if len(self._error_msg) > 0:
					message = "%s" % (self._error_msg,)
			else:
				#message = "(No LibWacom error)%s, at %s" % (self._error_msg, self._call)
				message = "%s, at %s" % (self._error_msg, self._call)
		else:
			if self._call is None:
				message = "(WacomErrorCode %i) - %s" % (self._error_code, self._error_msg)
			else:
				message = "(WacomErrorCode %i) - %s, at %s" % (self._error_code, self._error_msg, self._call)

		super(LibWacomError, self).__init__(message)

	# Returns a str 'function_name(argument_values...)'.
	def get_call_str(self, result, func, args):
		strargs = []
		for (num, arg) in enumerate(func.argtypes):
			# convert args to str for readable output
			if arg == c_char_p:
				strargs.append('"%s"' % args[num].decode("iso8859-1"))
			elif arg == c_void_p:
				try:
					# Ctypes native c_void_p can be casted to "int"
					strargs.append(hex(int(args[num])))
				except TypeError:
					# Other pointer objects fall here, and can't be casted to "int"
					strargs.append(hex(id(args[num])))
			else:
				strargs.append(str(args[num]))
		return "%s(%s)" % (func.__name__, ", ".join(strargs))


class LibWacom(LibraryWrapper):

	@staticmethod
	def _cdll():
		return ctypes.CDLL("libwacom.so.2", use_errno=True)

	_api_prototypes = {

		# WacomDeviceDatabase* libwacom_database_new(void)
		#
		# Loads the Tablet and Stylus databases to be used by libwacom.
		"libwacom_database_new": {
			"argtypes": (None),
			"restype": c_void_p,
			"errcheck": ctypes_errcheck
		},

		# WacomDeviceDatabase* libwacom_database_new_for_path(const char *datadir)
		#
		# Loads the Tablet and Stylus databases to be used by libwacom from the
		# prefix passed by "path".
		"libwacom_database_new_for_path": {
			"argtypes": (c_char_p,),
			"restype": c_void_p,
			"errcheck": ctypes_errcheck
		},

		# void libwacom_database_destroy(WacomDeviceDatabase *db)
		"libwacom_database_destroy": {
			"argtypes": (c_void_p,),
			"restype": None
		},

		# WacomDevice** libwacom_list_devices_from_database(const  WacomDeviceDatabase *db, WacomError *error)
		#
		# Returns the list of devices in the given database.
		# The list is an array of pointers to WacomDevice where the last 
		# element evaluates to False (Note this is not the same as None/NULL).
		#
		# Raises LibWacomError
		#
		# The list can be iterated with something like:
		#
		# 	lw = LibWacom()
		# 	db = lw.libwacom_database_new()
		# 	error = lw.libwacom_error_new()
		# 	list = None
		# 	
		# 	try:
		# 		i = 0
		# 		list = lw.libwacom_list_devices_from_database(db, error)
		# 		while True:
		# 			device_p = list[i]
		# 			if not bool(device_p): 
		# 				break
		# 			print i, "Device:", device_p.contents.name
		# 			i = i +  1
		# 	except LibWrapperException as lwe:
		# 		print lwe
		#
		# 	if bool(list): 
		# 		lw.libwacom_devices_list_destroy(device_p, deep = True)
		#
		# 	lw.libwacom_error_free(byref(error))
		# 	lw.libwacom_database_destroy(db)
		#
		# The list can also be iterated with a "for" loop in this fashion:
		#
		# 	i = 0
		# 	list = lw.libwacom_list_devices_from_database(db, error)
		# 	for device_p in list:
		# 		if not bool(device_p):
		# 			break
		# 		print i, lw.libwacom_get_name(device_p)
		# 		i = i + 1
		#
		# Note that "libwacom_get_name(device_p)" is the preferred way over
		# "device_p.contents.name"
		"libwacom_list_devices_from_database": {
			"argtypes": (c_void_p, POINTER(WacomError),),
			"restype": POINTER(POINTER(WacomDevice)),      # Raises LibWacomError
			#"errcheck": expect_not_none
			#"errcheck": ctypes_errcheck
			"errcheck": libwacom_errcheck    # TODO: add ctypes error check to libwacom_errcheck
		},


		# ---------------------------------------------------------------------------------------------------

		# WacomError* libwacom_error_new(void)
		"libwacom_error_new": {
			"argtypes": (None),
			#"restype": c_void_p
			"restype": POINTER(WacomError)
		},

		# void libwacom_error_free(WacomError **error)
		"libwacom_error_free": {
			#"argtypes": (POINTER(c_void_p),),
			"argtypes": (POINTER(POINTER(WacomError)),),
			"restype": None
		},

		# enum WacomErrorCode libwacom_error_get_code(WacomError *error)
		"libwacom_error_get_code": {
			#"argtypes": (c_void_p,),
			"argtypes": (POINTER(WacomError),),
			"restype": c_int
		},

		# const char* libwacom_error_get_message(WacomError *error)
		"libwacom_error_get_message": {
			#"argtypes": (c_void_p,),
			"argtypes": (POINTER(WacomError),),
			"restype": c_char_p,
			#"errcheck": expect_not_none   # Can be NULL when error->code == WERROR_NONE
		},

		# ---------------------------------------------------------------------------------------------------

		# WacomDevice* libwacom_new_from_path(const WacomDeviceDatabase *db, const char *path, WacomFallbackFlags fallback, WacomError *error)
		#
		# Returns a pointer to WacomDevice from the given device path. 
		# The "path" must be in the form of e.g. "/dev/input/event0".
		# "fallback" is whether we should create a generic if model is unknown.
		# In case the device is not found, None is returned. 
		# WERROR_INVALID_PATH indicates that a device was not found in the path
		# In case of error, a LibWacomError is risen.
		"libwacom_new_from_path": {
			#"argtypes": (c_void_p, c_char_p, c_int, c_void_p),
			"argtypes": (c_void_p, c_char_p, c_int, POINTER(WacomError)),
			#"restype": c_void_p,
			"restype": POINTER(WacomDevice),
			"errcheck": libwacom_errcheck_skip_invalid_path   # None for WERROR_INVALID_PATH, LibWacomError for WERROR_INVALID_DB
		},

		# WacomDevice* libwacom_new_from_usbid(const WacomDeviceDatabase *db, int vendor_id, int product_id, WacomError *error)
		#
		# Returns a pointer to WacomDevice from the given vendor/product IDs.
		# In case the device is not found, None is returned. 
		# In case of error, a LibWacomError is risen.
 		"libwacom_new_from_usbid": {
			#"argtypes": (c_void_p, c_int, c_int, c_void_p),
			"argtypes": (c_void_p, c_int, c_int, POINTER(WacomError)),
			#"restype": c_void_p,
			"restype": POINTER(WacomDevice),
			#"errcheck": expect_not_none    # None for WERROR_UNKNOWN_MODEL, LibWacomError for WERROR_INVALID_DB.
			"errcheck": libwacom_errcheck_skip_unknown    # None for WERROR_UNKNOWN_MODEL, LibWacomError for WERROR_INVALID_DB.
		},

		# WacomDevice* libwacom_new_from_name(const WacomDeviceDatabase *db, const char *name, WacomError *error);
 		"libwacom_new_from_name": {
			#"argtypes": (c_void_p, c_char_p, c_void_p),
			"argtypes": (c_void_p, c_char_p, POINTER(WacomError)),
			#"restype": c_void_p,
			"restype": POINTER(WacomDevice),
			#"errcheck": expect_not_none    # None for WERROR_UNKNOWN_MODEL, LibWacomError for WERROR_INVALID_DB.
			"errcheck": libwacom_errcheck_skip_unknown    # None for WERROR_UNKNOWN_MODEL, LibWacomError for WERROR_INVALID_DB.
		},

		# void libwacom_destroy(WacomDevice *device)
		"libwacom_destroy": {
			#"argtypes": (c_void_p,),
			"argtypes": (POINTER(WacomDevice),),
			"restype": None
		},

		# ---------------------------------------------------------------------------------------------------

		# void libwacom_print_device_description (int fd, const WacomDevice *device)
		"libwacom_print_device_description": {
			"argtypes": (c_int, c_void_p),
			"restype": None
		},

		# int libwacom_compare(const WacomDevice *a, const WacomDevice *b, WacomCompareFlags flags);
		#
		# Compare the two devices for equal-ness.
		# "flags" dictate what constitutes a match
 		# Returns 0 if the devices are identical, nonzero otherwise
 		"libwacom_compare": {
			"argtypes": (POINTER(WacomDevice), POINTER(WacomDevice), c_int),
			"restype": c_int,
			"errcheck": ctypes_errcheck
		},

		# WacomClass libwacom_get_class(const WacomDevice *device);
 		"libwacom_get_class": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int,
		},

		# const char* libwacom_get_name(const WacomDevice *device)
		"libwacom_get_name": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_char_p,
			"errcheck": expect_not_none
		},

		# const char* libwacom_get_layout_filename(const WacomDevice *device);
		#
		# Returns the full filename including path to the SVG layout of the 
		# device if available, or NULL otherwise
		"libwacom_get_layout_filename": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_char_p
		},

		# int libwacom_get_vendor_id(const WacomDevice *device);
		# 
		# Returns the numeric vendor ID for this device
		"libwacom_get_vendor_id": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int
		},

		# const char* libwacom_get_match(const WacomDevice *device);
		#
		# Returns the current match string used for this device (if set) or the
		# first match string in the tablet definition.
		"libwacom_get_match": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_char_p,
			"errcheck": expect_not_none
		},

		# const WacomMatch** libwacom_get_matches(const WacomDevice *device);
		#
		# Returns a pointer to the null-terminated list of possible matches for
		# this device. Do not modify this pointer or any content!
		# 
		# You can iterate the list with something like:
		#
		#   i = 0
		#   list = lw.libwacom_get_matches(device)
		#   while True:
		#   	match_p = list[i]
		#   	if not bool(match_p): 
		#   		break
		#   	print i, "Match:", match_p.contents.match
		#   	i = i + 1
		"libwacom_get_matches": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": POINTER(POINTER(WacomMatch)),
			"errcheck": ctypes_errcheck
		},

		# const WacomMatch* libwacom_get_paired_device(const WacomDevice *device);
		# 
		# A pointer to paired device for this device. 
		# A paired device is a device with a different match string but that 
		# shares the physical device with this device.
		# 
		# If the return value is NULL, no device is paired with this device or 
		# all paired devices have the same WacomMatch as this device.
		# 
		# The returned device may not be a libwacom device itself.
		# 
		# Do not modify this pointer or any content!
		#
		# TODO: If we enable this call, we get the following error when loading LibWacom():
		# AttributeError: /usr/lib/x86_64-linux-gnu/libwacom.so.2: undefined symbol: libwacom_get_paired_device
		# The error happens in libwrapper:    api_call = getattr(cls._loaded_lib, name)
		#
		#"libwacom_get_paired_device": {
		#	"argtypes": (POINTER(WacomDevice),),
		#	"restype": POINTER(WacomMatch),
		#	"errcheck": ctypes_errcheck
		#},

 		# int libwacom_get_product_id(const WacomDevice *device);
		"libwacom_get_product_id": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int
		},

		# int libwacom_get_width(const WacomDevice *device);
		# 
		# Returns the width of the device in inches. 
		# This is the width of the usable area as advertised, not the total 
		# size of the physical tablet.
		"libwacom_get_width": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int
		},

		# int libwacom_get_height(const WacomDevice *device);
		# 
		# Returns the height of the device in inches.
		# This is the height of the usable area as advertised, not the total 
		# size of the physical tablet.
		"libwacom_get_height": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int
		},

		# int libwacom_has_stylus(const WacomDevice *device);
		# 
 		# Returns non-zero if the device supports styli or zero otherwise
		"libwacom_has_stylus": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int
		},

		# int libwacom_has_touch(const WacomDevice *device);
		# 
		# Returns non-zero if the device supports touch or zero otherwise
		"libwacom_has_touch": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int
		},

		# int libwacom_get_num_buttons(const WacomDevice *device);
		# 
		# Returns the number of buttons on the tablet.
  		# Tablet buttons are numbered 'A' through to 'A' + number of buttons.
 		"libwacom_get_num_buttons": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int
		},

		# const int *libwacom_get_supported_styli(const WacomDevice *device, int *num_styli);
		# 
		# "num_styli" is the return location for the number of listed styli
		# Returns an array of Styli IDs supported by the device
		#
		# Use it something like this:
		#
		# 	num_styli = c_int(0)
		# 	styli = libwacom_get_supported_styli(device_p, byref(num_styli))
		# 	for n in range(num_styli.value):
		# 		print "Stylus %d: %d" % (n, styli[n])
 		"libwacom_get_supported_styli": {
			"argtypes": (POINTER(WacomDevice),POINTER(c_int)),
			"restype": POINTER(c_int),
			"errcheck": ctypes_errcheck
		},

		# int libwacom_has_ring(const WacomDevice *device);
		# 
		# Returns non-zero if the device has a touch ring or zero otherwise
  		"libwacom_has_ring": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_bool
		},

		# int libwacom_has_ring2(const WacomDevice *device);
		#
		# Returns non-zero if the device has a second touch ring or zero otherwise
  		"libwacom_has_ring2": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_bool
		},

		# int libwacom_has_touchswitch(const WacomDevice *device);
		# 
		# Returns non-zero if the device has a touch switch or zero otherwise
  		"libwacom_has_touchswitch": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_bool
		},

		# int libwacom_get_ring_num_modes(const WacomDevice *device);
		# 
		# the number of modes for the touchring if it has a mode switch
 		"libwacom_get_ring_num_modes": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int
		},

		# int libwacom_get_ring2_num_modes(const WacomDevice *device);
		# 
		# Returns the number of modes for the second touchring if it has a mode switch
  		"libwacom_get_ring2_num_modes": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int
		},

		# int libwacom_get_num_strips(const WacomDevice *device);
		# 
		# Returns the number of touch strips on the tablet otherwise
  		"libwacom_get_num_strips": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int
		},

		# int libwacom_get_strips_num_modes(const WacomDevice *device);
		# 
		# Returns the number of modes for each of the touchstrips if any
  		"libwacom_get_strips_num_modes": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int
		},

		# const WacomStatusLEDs *libwacom_get_status_leds(const WacomDevice *device, int *num_leds);
		# 
 		# "num_leds" is the return location for the number of supported status LEDs
 		# Returns an array of status LEDs supported by the device
		#
		# Use it something like this:
		#
		# 	num_leds = c_int(0)
		# 	leds = libwacom_get_status_leds(device_p, byref(num_leds))
		# 	for n in range(num_leds.value):
		# 		print "Status LED %d: %d" % (n, leds[n])
		#
  		"libwacom_get_status_leds": {
			"argtypes": (POINTER(WacomDevice), POINTER(c_int)),
			"restype": POINTER(c_int),
			"errcheck": ctypes_errcheck
		},

		# int libwacom_get_button_led_group (const WacomDevice *device, char button);
		# 
 		# "button" is the ID of the button to check for, between 'A' and 'Z'
 		# Returns the status LED group id to use or -1 if no LED is available 
		# for the given tablet / button
  		"libwacom_get_button_led_group": {
			"argtypes": (POINTER(WacomDevice), c_char),
			"restype": c_int
		},

		# int libwacom_is_builtin(const WacomDevice *device) LIBWACOM_DEPRECATED
		#
		# Returns non-zero if the device is built into the screen (ie a screen 
		# tablet) or zero if the device is an external tablet
		# 
 		# This function is deprecated. 
		# Use libwacom_get_integration_flags() instead.
		"libwacom_is_builtin": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int
		},
 
		# int libwacom_is_reversible(const WacomDevice *device);
		# 
		# Returns non-zero if the device can be used left-handed (rotated 180
		# degrees)
		"libwacom_is_reversible": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_bool
		},

		# WacomIntegrationFlags libwacom_get_integration_flags (const WacomDevice *device);
		# 
		# Returns the integration flags for the device
 		"libwacom_get_integration_flags": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int
		},

		# WacomBusType libwacom_get_bustype(const WacomDevice *device);
		# 
		# Returns the bustype of this device.
		"libwacom_get_bustype": {
			"argtypes": (POINTER(WacomDevice),),
			"restype": c_int
		},

		# WacomButtonFlags libwacom_get_button_flag(const WacomDevice *device, char button);
		#
		# "button" is the ID of the button to check for, between 'A' and 'Z'.
		# Returns a WacomButtonFlags with information about the button
 		"libwacom_get_button_flag": {
			"argtypes": (POINTER(WacomDevice), c_char),
			"restype": c_int
		},

		# const WacomStylus *libwacom_stylus_get_for_id (const WacomDeviceDatabase *db, int id);
		# 
		# Get the WacomStylus for the given tool ID.
		# "id" is the Tool ID for this stylus
		# Returns a WacomStylus representing the stylus. Do not free.
  		"libwacom_stylus_get_for_id": {
			"argtypes": (c_void_p, c_int),
			"restype": POINTER(WacomStylus),
			"errcheck": ctypes_errcheck
		}, 

		# int libwacom_stylus_get_id (const WacomStylus *stylus);
		# 
		# Returns the ID of the tool
		# Returns a WacomButtonFlags with information about the button
 		"libwacom_stylus_get_id": {
			"argtypes": (POINTER(WacomStylus),),
			"restype": c_int
		},

		# const char *libwacom_stylus_get_name (const WacomStylus *stylus);
		# Returns the name of the stylus
 		"libwacom_stylus_get_name": {
			"argtypes": (POINTER(WacomStylus),),
			"restype": c_char_p
		},

		# int libwacom_stylus_get_num_buttons (const WacomStylus *stylus);
		# 
		# Returns the number of buttons on the stylus
 		"libwacom_stylus_get_num_buttons": {
			"argtypes": (POINTER(WacomStylus),),
			"restype": c_int
		},

		# int libwacom_stylus_has_eraser (const WacomStylus *stylus);
		# 
		# Returns whether the stylus has an eraser
 		"libwacom_stylus_has_eraser": {
			"argtypes": (POINTER(WacomStylus),),
			"restype": c_bool
		},
 
		# int libwacom_stylus_is_eraser (const WacomStylus *stylus);
		# 
		# Returns whether the stylus is actually an eraser
 		"libwacom_stylus_is_eraser": {
			"argtypes": (POINTER(WacomStylus),),
			"restype": c_bool
		},

		# int libwacom_stylus_has_lens (const WacomStylus *stylus);
		# 
		# Returns whether the stylus has a lens
  		"libwacom_stylus_has_lens": {
			"argtypes": (POINTER(WacomStylus),),
			"restype": c_bool
		},

		# int libwacom_stylus_has_wheel (const WacomStylus *stylus);
		# 
		# Returns whether the stylus has a relative mouse wheel
 		"libwacom_stylus_has_wheel": {
			"argtypes": (POINTER(WacomStylus),),
			"restype": c_bool
		},

		# WacomAxisTypeFlags libwacom_stylus_get_axes (const WacomStylus *stylus);
		# 
		# Returns the flags specifying the list of absolute axes
  		"libwacom_stylus_get_axes": {
			"argtypes": (POINTER(WacomStylus),),
			"restype": c_int
		},

		# WacomStylusType libwacom_stylus_get_type (const WacomStylus *stylus);
		# 
		# Returns the type of stylus
   		"libwacom_stylus_get_type": {
			"argtypes": (POINTER(WacomStylus),),
			"restype": c_int,
			"errcheck": ctypes_errcheck
		},

		# void libwacom_print_stylus_description (int fd, const WacomStylus *stylus);
		# 
		# Prints the description of this stylus to the given file.
		# "fd" is the file descriptor
		# "stylus" is the stylus to print the description for.
    	"libwacom_print_stylus_description": {
			"argtypes": (c_int, POINTER(WacomStylus),),
			"restype": None,
			"errcheck": ctypes_errcheck
		},

		# const char *libwacom_match_get_name(const WacomMatch *match);
    	"libwacom_match_get_name": {
			"argtypes": (POINTER(WacomMatch),),
			"restype": c_char_p,
			"errcheck": ctypes_errcheck
		},

		# WacomBusType libwacom_match_get_bustype(const WacomMatch *match);
    	"libwacom_match_get_bustype": {
			"argtypes": (POINTER(WacomMatch),),
			"restype": c_int
		},

		# uint32_t libwacom_match_get_product_id(const WacomMatch *match);
    	"libwacom_match_get_product_id": {
			"argtypes": (POINTER(WacomMatch),),
			"restype": c_uint32
		},

		# uint32_t libwacom_match_get_vendor_id(const WacomMatch *match);
    	"libwacom_match_get_vendor_id": {
			"argtypes": (POINTER(WacomMatch),),
			"restype": c_uint32
		},

		# const char* libwacom_match_get_match_string(const WacomMatch *match);
    	"libwacom_match_get_match_string": {
			"argtypes": (POINTER(WacomMatch),),
			"restype": c_char_p
		},

		# ---------------------------------------------------------------------------------------------------

	}

	# TODO: ask in libwacom distro if we need to add this. 
	# "list" is a POINTER(POINTER(WacomDevice))
	# "deep" is a c_bool, indicates whether to also delete each WacomDevice
	# list = calloc (g_list_length (devices) + 1, sizeof (WacomDevice *));
	def libwacom_devices_list_destroy(self, list, deep = False):
		for device_p in list:
			if not bool(device_p):
				break
			if deep:
				self.libwacom_destroy(device_p)
			# TODO: delete here the list[i] elements
			# libwacom does not provide a delete function for this
			# we could load libc and call free 

	def get_error_message(self, error):
		_code = self.libwacom_error_get_code(error)
		_message = self.libwacom_error_get_message(error)
		if code == WacomErrorCode.WERROR_NONE:
			_message = "No error"
		return _code, ":", repr(_message)



