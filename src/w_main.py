# -*- Mode: Python; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*- #
# w_main.py
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

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GdkPixbuf, Gdk

class WMain():

	'''
	The main window (w_main) contains a main_notebook.
	The main_notebook contains a devices_notebook

	The devices_notebook contains a Mapping and a Information tab.
	The devices_notebook can get dynamically added:
	~ Tablet
	~ Stylus
	~ Touch
	'''

	MAIN_TAB_NODEVICE = 0
	MAIN_TAB_DEVICE = 1

	#UI_FILE = "/usr/local/share/gsetwacom/ui/w_main.ui"
	#UI_FILE = "src/w_main.ui"          # TODO: Use GResources
	UI_FILE = "w_main.ui"          # TODO: Use GResources

	def __init__(self, app):
		self._app = app 
		self._builder = app.get_gtk_builder()
		self._window = self._get_window_from_file(self.UI_FILE, "w_main", self)
		self._main_nb = self._builder.get_object("main_notebook")
		self._devices_nb = self._builder.get_object("devices_notebook")

		#self.add_page_from_ui_file("w_info.ui", "w_info", "Information")

		# TODO: add Mapping and Information tabs

	def show(self):
		self._window.show_all()

	def show_no_device_page(self):
		self.set_current_page(self.MAIN_TAB_NODEVICE)

	def show_device_page(self):
		self.set_current_page(self.MAIN_TAB_DEVICE)

	def set_current_page(self, id):
		#main_nb = self._builder.get_object("main_notebook")
		self._main_nb.set_current_page(id)
		
	def get_current_page(self):
		#main_nb = self._builder.get_object("main_notebook")
		return self._main_nb.get_current_page()

	# Adds a container panel to the devices notebook
	def add_page_from_ui_file(self, file, name, title):
		panel = self._get_window_from_file(file, name, self)
		self._devices_nb.append_page(panel, Gtk.Label(title))
		return panel

	# Adds a container panel to the devices notebook at the position indicated
	# page - a DevicePage object 
	def add_page(self, page, pos = -1):
		panel = page.get_panel()
		title = page.get_title()
		self._devices_nb.insert_page(panel, Gtk.Label(title), pos)
		
	# Retrieves a window from the Gtk builder and connect signals if signals_map is passed
	# The window can actually be any of the Gtk.Box children.
	# file - name of the Glade file containing the window
	# name - id of the window in the file
	# signals_map - dictionary or Python object that contains the callbacks referred in the file
	def _get_window_from_file(self, file, name, signals_map = None):
		basepath = os.path.abspath(os.path.dirname(__file__))

		# TODO: check if the file has been added before
		self._builder.add_from_file(basepath + "/" + file)

		if not signals_map == None:
			self._builder.connect_signals(signals_map)

		return self._builder.get_object(name)	

	def set_device_title(self, title):
		l_device_title = self._builder.get_object("l_device_title")
		l_device_title.set_text(title)

	# Callbacks 

	def on_window_destroy(self, window):
		self._app.quit()

