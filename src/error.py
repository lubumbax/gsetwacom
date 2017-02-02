# -*- Mode: Python; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*- #
# error.py
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

class GsException(Exception):
	''' 
	GsException is a base Exception for all Py GSetWacom operations
	'''
	pass

class GsError(GsException):
	'''
	GsError and subclasses indicate a "non recoverable" error.
	Typically, the application breaks after one of these.
	'''

	def __init__(self, description, reason = None):
		if reason is None:
			message = "%s" % (description)
		else:
			message = "%s\nReason:\n%s" % (description, str(reason))
			
		super(GsError, self).__init__(message)


