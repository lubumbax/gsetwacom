# -*- Mode: Python; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*- #
# device_pages.py
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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class DevicePage(object):
	def __init__(self, device_id, n = 0, type_tag = "generic", title = "Page"):

		self._type_tag = type_tag
		self._n = str(n)
		self._device_id = device_id

		# A page id is made of 'type_tag:n:device_id' where 'n' is the number
		# of panel of a particular type for a device
		#self._id = id

		self._title = title
		self._box = Gtk.Box(Gtk.Orientation.VERTICAL, spacing=0)

	def get_id(self):
		return self._type_tag + ':' + self._n + ':' + self._device_id

	def get_panel(self):
		return self._box

	def get_title(self):
		return self._title


class PageTablet(DevicePage):
	def __init__(self, device_id, n = 0, title = "Tablet"):
		super(PageTablet, self).__init__(device_id, n, "tablet", title)

		box = self.get_panel()

		label1 = Gtk.Label("Not implemented")
		box.pack_start(label1, True, True, 0)


class PageStylus(DevicePage):
	def __init__(self, device_id, n = 0, title = "Stylus"):
		super(PageStylus, self).__init__(device_id, n, "stylus", title)

		box = self.get_panel()

		label1 = Gtk.Label("Not implemented")
		box.pack_start(label1, True, True, 0)


class PageTouch(DevicePage):
	def __init__(self, device_id, n = 0, title = "Touch"):
		super(PageTouch, self).__init__(device_id, n, "touch", title)

		box = self.get_panel()

		label1 = Gtk.Label("Not implemented")
		box.pack_start(label1, True, True, 0)


class PageMapping(DevicePage):
	def __init__(self, device_id, n = 0, title = "Mapping"):
		super(PageMapping, self).__init__(device_id, n, "mapping", title)

		box = self.get_panel()

		label1 = Gtk.Label("Not implemented")
		box.pack_start(label1, True, True, 0)


class PageInformation(DevicePage):
	def __init__(self, device_id, n = 0, title = "Information"):
		super(PageInformation, self).__init__(device_id, n, "info", title)

		box = self.get_panel()

		label1 = Gtk.Label("Not implemented")
		box.pack_start(label1, True, True, 0)
