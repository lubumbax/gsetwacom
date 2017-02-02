# -*- Mode: Python; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*- #
# logger.py
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
import sys
import traceback

LEVEL_FATAL   = 0
LEVEL_ERROR   = 1
LEVEL_WARNING = 2
LEVEL_INFO    = 3
LEVEL_DEBUG   = 4

class Logger():

	_tags = {
		LEVEL_FATAL   : "FATAL  ",
		LEVEL_ERROR   : "ERROR  ",
		LEVEL_WARNING : "WARNING",
		LEVEL_INFO    : "INFO   ",
		LEVEL_DEBUG   : "DEBUG  "
	}

	# TODO: implement logging to file, and/or a way to indicate where to send 
	# logs to (console only, file only, both).
	
	def __init__(self, level = LEVEL_WARNING):
		# parse number in case we have entered string (eg: 'info')
		if isinstance(level, basestring):
			level = self._parse_level_str(level)

		self._level = level                # logger debug level
		self._print_level = True           # include level tag

	# Allows for including or excluding the "level tag" in the log line
	def set_print_level(self, print_level = True):
		self._print_level = print_level

	def fatal(self, message, exception = None):
		if self._level < LEVEL_FATAL:
			return
			
		self._print_message(self._tags[LEVEL_FATAL], message)
		if not exception is None:
			self._print_exception(exception)

	def error(self, message, exception = None):
		if self._level < LEVEL_ERROR:
			return
			
		self._print_message(self._tags[LEVEL_ERROR], message)
		if not exception is None:
			self._print_exception(exception)
		
	def warning(self, message, exception = None):
		if self._level < LEVEL_WARNING:
			return
			
		self._print_message(self._tags[LEVEL_WARNING], message)
		if not exception is None:
			self._print_exception(exception)
		
	def info(self, message, exception = None):
		if self._level < LEVEL_INFO:
			return
		
		self._print_message(self._tags[LEVEL_INFO], message)
		if not exception is None:
			self._print_exception(exception)
		
	def debug(self, message, exception = None):
		if self._level < LEVEL_DEBUG:
			return

		self._print_message(self._tags[LEVEL_DEBUG], message)
		if not exception is None:
			self._print_exception(exception)

	# Logs no matter what. 
	def log(self, message):			
		#self._send_to_log(message)
		self._send_to_log("          | %s" % (message))


	# Sends "line" to the log. 
	# For now we just send to stdout but in the future we will want to 
	# add functionality to our logger so that it sends to a log file.
	# This is the function that will do that.
	def _send_to_log(self, line):
		print line

	def _print_message(self, tag, message):
		if self._print_level:
			self._send_to_log("%s | %s" % (tag, message))
		else:
			self._send_to_log(message)

	def _print_exception(self, exception):
		sys.last_type, sys.last_value, sys.last_traceback = sys.exc_info()

		self._send_to_log("          |   %s: %s" % (sys.last_type.__name__, exception))
		self._send_to_log("          |")

		#lines = traceback.format_exception(sys.last_type, sys.last_value, sys.last_traceback)
		#for line in lines:
		#	for part in line.split('\n'):
		#		self._send_to_log("          | %s" % (part))

		tuples = traceback.extract_tb(sys.last_traceback)
		for filename, line_number, function, text in tuples:
			self._send_to_log("          |   %s:%d" % (filename, line_number))
			self._send_to_log("          |     %s" % (text))

		self._send_to_log("          |")

	def _parse_level_str(self, level, default = LEVEL_WARNING):
		if str.upper(level) == "FATAL":
			return LEVEL_FATAL
		elif str.upper(level) == "ERROR":
			return LEVEL_ERROR
		elif str.upper(level) == "WARNING":
			return LEVEL_WARNING
		elif str.upper(level) == "INFO":
			return LEVEL_INFO
		elif str.upper(level) == "DEBUG":
			return LEVEL_DEBUG
		else:
			return default

