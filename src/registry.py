# -*- Mode: Python; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*- #
# registry.py
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

from threading import Lock, RLock
from error import GsException, GsError


class GsRegistryException(GsException):
	pass

class GsRegistryLocked(GsRegistryException):
	pass

class GsNoTransaction(GsRegistryException):
	def __init__(self, message = ""):			
		super(GsNoTransaction, self).__init__("Not in transaction. %s" % (message))


class DeviceRegistry():

	'''
	DeviceRegistry keeps track of discovered Devices and their status. 

	This class lets us know what devices are newly discovered (new), well 
	existing (running), are not available in the system anymore (deleted) or
	set to be availability-checked. 

	The devices tracked by the registry are added, updated or removed within
	transactions. 
	Devices are registered during a transaction. At the end of each transaction 
	the registry checks with of the registered devices are new, were already 
	existing, or which ones are missing.

	The registry is by default 'sticky', meaning that devicees that have gone
	missing are kept in the registry as missing. This is the way the app can
	reuse the data of the device in the registry to reconfigure the device if
	it comes back to life again.

	In most cases the registry will contain just one device.

	The registry is transactional, meaning that it can be set to take changes,
	keep track of the changes and persist (TODO: implement rollback) the 
	changes.

	A typical flow of operation can be:

		registry.begin()                       #1: acquire lock, impl. CHECKING
		registry.start_checking()              #2: all to CHECKING
		devices = app.find_devices()           #3
		for device in devices:
			registry.register(device)          #4: found ones to NEW or RUNNING
		registry.end_checking()                #5: all CHECKING ones to DELETED
		app.notify_devices(..)                 $6
		registry.commit()                      #7: NEW to RUNNING, DELETED ones
	                                               are removed, lock released.
	
	This is what that does:
	~ [#1] Firstly we begin the transaction, which acquires a lock so that no 
	  other concurrent thread corrupts the registry.
	  By default, begin() calls start_checking() implicitly. That means that 
	  all Devices in the registry are set to STATUS_CHECKING here as well.
	  We can set begin() to not run an implicit start_checking() by calling it
	  with "begin(false)".
	~ [#2] We set all Devices in the registry to STATUS_CHECKING. This is not 
	  needed if we let the default begin() do it implicitly (see prev. step).
	  From here, all existing Devices in the registry have to be registered 
	  again. Any not re-registered Device will be marked as deleted. Devices 
	  that have not been re-registered will also be marked as zoombie if the 
	  registry is 'zoombie'. In the end, devices marked as deleted will be 
	  removed.
	  Trying to retrieve a Device that is in STATUS_CHECKING will raise an
	  exception (TODO: this has to be determined) (GsDeviceOnChecking:GsError)
	~ [#3] Then the application finds devices available in the system.
	~ [#4] Then we register each of the devices available in the system.
	  That confirms those existing in the registry as still available to the 
	  application by marking them as STATUS_RUNNING.
	  Those that have the zoombie bit are considered 'resurrected'.
	  Those that were not existing in the registry are added as STATUS_NEW.
	~ [#5] Once we are done registering found devices we set those still existing
	  in the registry as STATUS_CHECKING to STATUS_DELETED. 
	  At this point they are set to be removed and by no means retrievable. 
	~ [#6] At this point the registry knows what devices are new (NEW), which 
	  ones are already existing before start_checking (RUNNING), or which ones 
	  are not available (DELETED) any more.
	  The application can be notified of these changes here.
	~ [#7] Finally, all devices on STATUS_NEW are set to STATUS_RUNNING and 
	  devices on STATUS_DELETED are removed.
	  If we call commit() without having called end_checking() before, commit()
	  does that automatically. That grants that no device is in CHECKING yet.


	Registering a device out of a transaction adds it as NEW. It is up to us to
	notify the application of this new Device. 
	Devices registered out of a transaction will be set to RUNNING once a 
	transaction is started. That means that these Devices will be considered 
	as "long existing".

	In normal operation (before begin() and after commit()/rollback()), all 
	existing Devices are supposed to be in STATUS_RUNNING.

	TODO: implement rollback(). Not sure that will be too useful. 
	Without having studied yet how "rollback" could be implemented, I suspect
	that it would make the other Registry transaction operations (begin, 
	register, commit) a bit more expensive. 
	Thus, still to be determined if this is worth to be implemented.

	TODO: implement locking on the class level, probably. 
	I don't see why someone would have two Registries, but in case that happens
	we maybe don't want to allow a 2nd registry to run transactions 
	concurrently with the 1st registry. 
	Actually I don't see why not. Transactions should be able to run 
	concurrently, each one in its own Registry. Whatever (the app?) runs a
	transaction in a particular registry is maybe what has to run synchronized 
	so that the registry is not corrupted. So it sounds like the mutex has to 
	exist at the instance level.
	I would say that synchronization has to happen in DeviceBroker.
	'''

	# Status of Devices in the registry
	STATUS_NONE        = 0       # No status. Ignore this device.
	STATUS_NEW         = 1 << 1  # just registered, not commited.
	STATUS_RUNNING     = 1 << 2  # registered and commited (long running).
	STATUS_CHECKING    = 1 << 3  # was running, set to be checked (may or may not be found)
	STATUS_CHANGED     = 1 << 4  # found in the system with hardware changes
	STATUS_DIRTY       = 1 << 5  # set by the app as changed properties
	STATUS_DELETED     = 1 << 6  # checked, not found, not commited yet (to be removed if 'sticky = False')
	STATUS_TURNING     = 1 << 7  # turning into zoombie
	STATUS_ZOOMBIE     = 1 << 8  # checked, not found, not commited yet (to be removed if 'sticky = False')
	STATUS_RESURRECTED = 1 << 9  # checked, not found, commited (persisted if 'sticky = True')

	# Transaction status
	TRANSACTION_STATUS_NONE     = 1 << 0	# set by commit(), and initial
	TRANSACTION_STATUS_BEGIN    = 1 << 1    # set by begin()
	TRANSACTION_STATUS_CHECKING = 1 << 2    # set by start_checking()
	TRANSACTION_STATUS_CKECKED  = 1 << 3    # set by end_checking()

	def __init__(self, sticky = True):
		'''
		self._registry = {
		    "device_id": {
		        "status": STATUS_NEW,
				"device": Device object
		    }
		}
		'''
		self._sticky = sticky
		self._registry = {}	
		self._reg_lock = RLock()

		self._tx_lock = Lock()
		self._transaction_status = self.TRANSACTION_STATUS_NONE

		# Initially, _registry_backup will be a copy of _registry at the time a
		# transaction started. Eventually, if we ever support multi-transaction
		# it will contain copies of each _registry at the time each transaction
		# started, identified by the tid (transaction id).
		# _registry_backup = { "t-001": {...}, "t-002"" {...}, ...}
		self._registry_backup = {}  # Used by rollback. It has to be empty when not in transaction. 

		self._observers = []
		
	def __del__(self):
		#self._lw.libwacom_database_destroy(self._db)
		pass

	# Begins a devices register transaction in the registry. 
	# 
	# Acquires the lock and, if "checking_implicit" is true, sets existing 
	# devices to CHECKING.
	#
	# Any concurrent thread trying to begin() a transaction on this Registry 
	# will have to queue until the thread owning the lock has released it by 
	# calling commit().
	# Any concurrent thread trying to perform a transaction operation other
	# than begin() or register() at this point will result in a GsNoTransaction exception.
	# Note that "register()" is allowed out of transaction, but that has 
	# implications. See class description above for more details.
	def begin(self, checking_implicit = True):
		# TODO: decide: calling begin(), if we already are in the middle of a 
		# transaction, should rollback() and then begin() a new transaction?
		# For now we just return doing nothing in case we already were in a 
		# transaction.
		if not self._transaction_status == self.TRANSACTION_STATUS_NONE:
			return

		self._tx_lock.acquire()
		self._transaction_status = self.TRANSACTION_STATUS_BEGIN
		self._backup()

		if checking_implicit is True:
			self.start_checking()

		# TODO: functionality: 
		# return here a transaction number or transaction-id.

	# Starts a "checking cycle" of devices in the registry.
	#
	# At the beginning of a checking cycle all existing devices in the registry
	# are supposed to be in RUNNING or ZOOMBIE status.
	# All existing devices are enabled the CHECKING status here.
	# Raises GsNoTransaction if begin() has not been called previously.
	def start_checking(self):
		if self._transaction_status < self.TRANSACTION_STATUS_BEGIN:
			raise GsNoTransaction("can't start checking if not in a transaction")
		self._add_devices_status(self.STATUS_CHECKING)
		self._transaction_status = self.TRANSACTION_STATUS_CHECKING

	# Handles registration of an incoming device, as it is discovered by the
	# application.
	#
	# 1) During registration, an incoming device is matched to registered devices
	# firstly by devices' internal id (which is by now made of "vendor:model").
	# 2) Once a device is found a match in the registry they are compared for 
	# hardware characteristics (a new sub-device may have been attached or 
	# removed). As a result, we have two kind of device match:
	# - Soft match (soft-hw-match): device matches by id only.
	# - Full match (soft-hw-match): device matches both by id and hardware.
	# 3) Once the hardware characteristics of a match are compared, the 
	# configuration (parameters configurable by the application) of the device
	# are compared:
	# - Config match (config-match): device matches configuration.
	#
	# Depending on the results of these comparison, this function does the 
	# following:
	# If no match at all is found, registers the device as NEW.
	# If a match is found:
	# ~ 'full-hw-match' and 'config-match': 
	#     leave the existing one and set it to RUNNING.
	#     that confirms the existing as available to the app without changes.
	# ~ 'full-hw-match' and no 'config-match': 
	#     leave the existing one and set it to RUNNING + DIRTY.
	#     that confirms the existing as available but has user configuration.
	# ~ 'soft-hw-match' and 'config-match':
	#     leave the existing one and set it to RUNNING + CHANGED.
	#     that confirms the existing as available but has hardware changes.
	# ~ 'soft-hw-match' and no 'config-match': 
	#     leave the existing one and set it to RUNNING + CHANGED + DIRTY.
	#     that confirms the existing as available but has hardware changes plus
	#     user configuration.
	#
	# If this method is called within a transaction:
	# - the app will be notified of new devices once the 'check cycle' finishes
	# - the new devices will be marked RUNNING once the transaction is commited
	# If this method is called not within a transaction:
	# - the new devices will be left with a NEW status
	# - it's up to the caller now to notify the app of new devices
	def register(self, device):
		self._register_device(device)

	# Evaluates changes in the registry since the check cycle started and 
	# notifies the application of the changes and removes non-existant devices 
	# conveniently.
	#
	# Here is how the observers (application) are notified:
	# ~ NEW devices:           notify_new
	# - RESURRECTED devices:   notify_resurrected
	# ~ RUNNING and CHANGED:   notify_changed
	# ~ RUNNING and DIRTY:     notify_dirty
	# ~ RUNNING and ZOOMBIE:   notify_zoombie
	# ~ DELETED:               notify_remove
	#
	# Devices still in CHECKING means haven't been registered so most likely
	# they are not present in the system, thus they are set to DELETED so that
	# they will be removed from the registry by commit().
	# In 'sticky' mode these devices are set to ZOOMBIE instead, so that
	# they won't be removed by commit(). This is done so to persist the user's
	# configuration changes done to a device from the UI, should the device 
	# 'resurrect'.
	#
	# In the end we will have some devices in NEW, RUNNING, DELETED or ZOOMBIE.
	# Raises GsNoTransaction if begin() has not been called previously.
	def end_checking(self):
		if self._transaction_status < self.TRANSACTION_STATUS_BEGIN:
			raise GsNoTransaction("can't end checking if not in a transaction")

		self._checking_to_deleted()
		self._notify()

		self._transaction_status = self.TRANSACTION_STATUS_CKECKED

	# Persists changes to the registry and notifies observers of changes.
	# 
	# The lock is released here so that other queueing concurrent threads can
	# begin() transactions in this registry.
	#
	# Here is what happens to each device attending to its status:
	# ~ NEW: set to RUNNING
	# ~ RUNNING and CHANGED/DIRTY: set to RUNNING only.
	# ~ DELETED: removed
	# ~ ZOOMBIE: set to RUNNING
	#
	# Raises GsNoTransaction if begin() has not been called previously.
	def commit(self):
		if self._transaction_status < self.TRANSACTION_STATUS_BEGIN:
			raise GsNoTransaction("can't commit if not in a transaction")

		if self._transaction_status < self.TRANSACTION_STATUS_CKECKED:
			self._checking_to_deleted()
			self._transaction_status = self.TRANSACTION_STATUS_CKECKED

		self._internal_commit()

		self._registry_backup = {}
		self._tx_lock.release()
		self._transaction_status = self.TRANSACTION_STATUS_NONE

	def rollback(self):
		if self._transaction_status < self.TRANSACTION_STATUS_BEGIN:
			raise GsNoTransaction("can't rollback if not in a transaction")
		else:
			self._restore()
			self._registry_backup = {}
			self._tx_lock.release()
			self._transaction_status = self.TRANSACTION_STATUS_NONE

	# Makes a "half-deep" copy of the registry (does not create copies of 
	# the Device objects).
	def _backup(self):
		#raise GsError("Badass")
		self._registry_backup = {}
		self._reg_lock.acquire()
		for id in self._registry:
			self._registry_backup[id] = { self._registry[id]['status'], self._registry[id]['device'] }
		self._reg_lock.release()
	
	def _restore(self):
		self._registry = {}
		self._reg_lock.acquire()
		for id in self._registry_backup():
			self._registry[id] = { self._registry_backup[id]['status'], self._registry_backup[id]['device'] }
		self._reg_lock.release()

	# Internal adds or updates an incoming device in the registry along with
	# its status.
	#
	# The behaviour of this method is conditioned by:
	# ~ whether the incoming device matches the hardware characteristics of a 
	#   registered one fully or partially (full vs soft match).
	# ~ in case there is a hardware match (full or soft), whether the 
	#   incoming device matches the configuration of the registered one.
	#
	# See a more detailed description ot #DeviceRegistry.register()
	#
	# [IMPORTANT TODO]: 
	# So far we consider "soft matches" as "full matches" until we decide 
	# adding support to detect and handle changes in the "hardware" of already 
	# existing devices. 
	# In general, there is much behaviour that we still have to determine 
	# regarding changes in the system (multiple devices, etc...).
	# This behaviour will have to be determined as we gain experience with 
	# libwacom and the possible Wacom devices out there.
	# libwacom developers are very welcome here! :)
	def _register_device(self, device):
		id = device.get_id()

		self._reg_lock.acquire()

		existing = self._get_device_by_id(id)
		if not existing:
			# No match
			self._registry[id] = { 'status': self.STATUS_NEW, 'device': device }
		else:

			# Here is where we want to see if the existing record vs the device
			# in the system are exactly the same or there are some changes like
			# the device in the system has one more pen, or an airbrush is gone
			# For now we assume that they are exactly the same (just match 'id')		
			# Otherwise, if "id" matches but there were chardware changes we 
			# mark the existing record as CHANGED

			# Override any other possible status flag with RUNNING
			#if self._device_is_zoombie(id):
			if self._device_is_zoombie(id):
				self._set_device_status(id, self.STATUS_RESURRECTED)
			else:
				self._set_device_status(id, self.STATUS_RUNNING)

			# Full hardware match
			if device.matches_full_hardware(existing):
				if not device.matches_configuration(existing):
					self._add_device_status(id, self.STATUS_DIRTY)
			# Soft hardware match
			else:
				self._add_device_status(id, self.STATUS_CHANGED)
				if not device.matches_configuration(existing):
					self._add_device_status(id, self.STATUS_DIRTY)

		self._reg_lock.release()

	# Sets devices on NEW to RUNNING and removes those on DELETED.
	# It also removes extra flags 
	def _internal_commit(self):
		self._reg_lock.acquire()

		for id in self._registry.keys():
			# Set devices on ZOOMBIE and RUNNING to only ZOOMBIE here so that
			# they don't trigger _notify() on a next check cycle (unless they 
			# have been resurrected)
			if self._registry[id]['status'] == self.STATUS_TURNING:
				self._registry[id]['status'] = self.STATUS_ZOOMBIE

			# Set ZOOMBIE, CHANGED and DIRTY devices to RUNNING here so that
			# they don't trigger _notify() on a next check cycle
			if self._registry[id]['status'] & (self.STATUS_CHANGED | self.STATUS_DIRTY):
				self._registry[id]['status'] = self.STATUS_RUNNING

			# NEWly discovered devices have been notified so they are now
			# set to RUNNING
			if self._registry[id]['status'] == self.STATUS_NEW:
				self._registry[id]['status'] = self.STATUS_RUNNING

			# DELETED devices are removed from the registry.
			if self._registry[id]['status'] == self.STATUS_DELETED:
				del self._registry[id]

		self._reg_lock.release()

	def _get_device_by_id(self, id):
		record = self._registry.get(id)
		if not record is None:
			return record['device']
		else:
			return None

	def _set_device_status(self, id, status):
		record = self._registry.get(id)
		self._reg_lock.acquire()
		if not record is None:
			record['status'] = status
		self._reg_lock.release()

	def _set_devices_status(self, status):
		self._reg_lock.acquire()
		for id in self._registry:
			self._registry[id]['status'] = status
		self._reg_lock.release()

	def _add_devices_status(self, status):
		self._reg_lock.acquire()
		for id in self._registry:
			self._registry[id]['status'] = self._registry[id]['status'] | status
		self._reg_lock.release()

	#def _del_devices_status(self, status):
	#	self._reg_lock.acquire()
	#	for id in self._registry:
	#		self._registry[id]['status'] = self._registry[id]['status'] & !status
	#	self._reg_lock.release()

	# Sets devices that are still in CHECKING status to DELETED.
	# If the registry is 'sticky' set devices to ZOOMBIE.
	def _checking_to_deleted(self):
		self._reg_lock.acquire()
		for id in self._registry:
			if self._registry[id]['status'] & self.STATUS_CHECKING and not \
			   self._registry[id]['status'] & self.STATUS_ZOOMBIE:
				if self._sticky:
					self._registry[id]['status'] = self.STATUS_TURNING
				else:
					self._registry[id]['status'] = self.STATUS_DELETED
		self._reg_lock.release()

	def _device_is_zoombie(self, id):
		record = self._registry.get(id)
		if not record is None:
			return record['status'] & self.STATUS_ZOOMBIE
		else:
			return False

	def get_devices_running(self):
		devices = []
		self._reg_lock.acquire()
		for id in self._registry:
			if self._registry[id]['status'] & self.STATUS_RUNNING:
				devices.append(self._registry[id]['device'])
		self._reg_lock.release()
		return devices

	def get_devices_new(self):
		devices = []
		self._reg_lock.acquire()
		for id in self._registry:
			if self._registry[id]["status"] & self.STATUS_NEW:
				devices.append(self._registry[id]['device'])
		self._reg_lock.release()
		return devices

	def get_devices_deleted(self):
		devices = []
		self._reg_lock.acquire()
		for id in self._registry:
			if self._registry[id]["status"] & self.STATUS_DELETED:
				devices.append(self._registry[id]['device'])
		self._reg_lock.release()
		return devices

	def add_observer(self, observer):
		self._observers.append(observer)

	# Notifies observers of changes in the registry
	# ~ NEW devices:          notify_new
	# - RESURRECTED devices:  notify_resurrected
	# ~ RUNNING and CHANGED:  notify_changed
	# ~ RUNNING and DIRTY:    notify_dirty
	# ~ RUNNING and ZOOMBIE:  notify_zoombie
	# ~ DELETED (removed):    notify_removed
	def _notify(self):
		for id in self._registry:
			for observer in self._observers:
				if self._registry[id]['status']   == self.STATUS_NEW:
					self._notify_observer(observer, 
					                      'notify_device_new', 
					                      self._registry[id]['device'])
				elif self._registry[id]['status'] == self.STATUS_RESURRECTED:
					self._notify_observer(observer, 
					                      'notify_device_resurrected', 
					                      self._registry[id]['device'])
				elif self._registry[id]['status'] & (self.STATUS_RUNNING | self.STATUS_CHANGED):
					self._notify_observer(observer, 
					                      'notify_device_changed', 
					                      self._registry[id]['device'])
				elif self._registry[id]['status'] & (self.STATUS_RUNNING | self.STATUS_DIRTY):
					self._notify_observer(observer, 
					                      'notify_device_dirty', 
					                      self._registry[id]['device'])
				elif self._registry[id]['status'] == self.STATUS_TURNING:
					self._notify_observer(observer, 
					                      'notify_device_zoombie', 
					                      self._registry[id]['device'])
				elif self._registry[id]['status'] == self.STATUS_DELETED:
					self._notify_observer(observer, 
					                      'notify_device_deleted', 
					                      self._registry[id]['device'])

	def _notify_observer(self, observer, event_name, device):
		observer_callback = getattr(observer, "on_" + event_name, None)
		if callable(observer_callback):
			result = observer_callback(device)
