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

class WMain():

	#UI_FILE = "/usr/local/share/gsetwacom/ui/w_main.ui"
	UI_FILE = "src/w_main.ui"          # TODO: Use GResources

	def __init__(self, app):
		self._app = app
		self._window = self._app.get_window_from_file(self.UI_FILE, "w_main", self)

		#''' Instantiate the preferences dialog '''
		#self.d_prefs = preferences.DlgPreferences(self.app)
		#''' Instantiate the computers factory dialog '''
		#self.d_factory = factory.DlgFactory(self.app)
		#''' Instantiate the about dialog '''
		#self.d_about = self.app.builder.get_object("w_about")

	def show(self):
		self._window.show_all()

	def on_window_destroy(self, window):
		self._app.quit()

