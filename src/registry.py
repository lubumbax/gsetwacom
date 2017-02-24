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


TRANSACTION_STATUS_NONE     = 1 << 0	# set by commit(), and initial
TRANSACTION_STATUS_BEGIN    = 1 << 1    # set by begin()
TRANSACTION_STATUS_CHECKING = 1 << 2    # set by start_checking()
TRANSACTION_STATUS_CKECKED  = 1 << 3    # set by end_checking()


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
	In most cases the registry will contain just one device.

	The registry is transactional, meaning that it can be set to take changes,
	keep track of the changes and persist (TODO: implement rollback) the 
	changes.

	A typical flow of operation can be:

		registry.begin()                       #1: acquire lock, impl CHECKING
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
	  By default, begin() has start_checking() implicit. That means that all 
	  Devices in the registry are set to STATUS_CHECKING here as well.
	  We can set begin to not run an implicity start_checking() by calling it
	  with "begin(false)".
	~ [#2] We set all Devices in the registry to STATUS_CHECKING. This is not 
	  needed if we let the default begin() do it implicitly (see prev. step).
	  From here, all existing Devices in the registry have to be registered 
	  again. Any not re-registered Device will be removed later. 
	  Trying to retrieve a Device that is in STATUS_CHECKING will raise an
	  exception (TODO: this has to be determined) (GsDeviceOnChecking:GsError)
	~ [#3] Then the application finds devices available in the system.
	~ [#4] Then we register each of the devices available in the system.
      That confirms those existing in the registry as still available to the 
	  application by marking them as STATUS_RUNNING.
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

	# REMOVE THESE 
	#self.STATUS_NEW       = 'N'    # A device is new in the registry, and is not commited yet.
	#self.STATUS_RUNNING   = 'R'    # A device is registerted and commited. 
	#self.STATUS_DELETED   = 'D'    # A device that doesn't belong to the registry any more, and has to be removed on commit. 
	#self.STATUS_CHECKING  = 'C'    # A device that is not available, but not deleted yet. It still has a chance to be returned to running. 

	STATUS_DELETED   = 1 << 0                   # checked, not found, not commited yet (to be removed)
	STATUS_NEW       = 1 << 1                   # just registered, not commited.
	STATUS_RUNNING   = 1 << 2                   # registered and commited. 
	STATUS_CHANGED   = 1 << 3 | STATUS_RUNNING  # found in the system with changes
	STATUS_DIRTY     = 1 << 4 | STATUS_RUNNING  # set by the app as changed properties
	STATUS_CHECKING  = 1 << 8 | STATUS_RUNNING  # was running, set to be checked (may or may not be found)

	def __init__(self):
		'''
		self._registry = {
		    "device_id": {
		        "status": STATUS_NEW,
				"device": Device object
		    }
		}
		'''
		self._registry = {}	
		self._reg_lock = RLock()

		self._tx_lock = Lock()
		self._transaction_status = TRANSACTION_STATUS_NONE

		# Initially, _registry_backup will be a copy of _registry at the time a
		# transaction started. Eventually, if we ever support multi-transaction
		# it will contain copies of each _registry at the time each transaction
		# started, identified by the tid (transaction id).
		# _registry_backup = { "t-001": {...}, "t-002"" {...}, ...}
		self._registry_backup = {}  # Used by rollback. It has to be empty when not in transaction. 
		
	def __del__(self):
		#self._lw.libwacom_database_destroy(self._db)
		pass

	# Acquires the lock and sets existing devices to CHECKING, unless 
	# "checking_implicit" is false.
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
		if not self._transaction_status == TRANSACTION_STATUS_NONE:
			return

		self._tx_lock.acquire()
		self._transaction_status = TRANSACTION_STATUS_BEGIN
		self._backup()

		if checking_implicit is True:
			self.start_checking()

		# TODO: functionality: 
		# return here a transaction number or transaction-id.

	# Sets all devices to CHECKING. 
	# Raises GsNoTransaction if begin() has not been called previously.
	def start_checking(self):
		if self._transaction_status < TRANSACTION_STATUS_BEGIN:
			raise GsNoTransaction("can't start checking if not in a transaction")
		self._set_devices_status(self.STATUS_CHECKING)                              # was: _set_devices_status_to_checking()
		self._transaction_status = TRANSACTION_STATUS_CHECKING

	# In a transaction, registers a device as NEW if it wasn't existing in the
	# registry before.
	# If the device was existing in the registry before, set it to RUNNING. 
	# That confirms those existing as still available to the application.
	#
	# If not in a transaction, it also adds the device as NEW. 
	# But it is up to the caller to notify the app of such a new Device. 
	# These devices will be set to RUNNING once a ransaction is started. That 
	# means that these Devices will be considered as "long existing".
	def register(self, device):
		self._register_device(device)

	# Set all CHECKING devices to DELETED.
	# This can be seen as a first stage of "garbage collection".
	# Raises GsNoTransaction if begin() has not been called previously.
	def end_checking(self):
		if self._transaction_status < TRANSACTION_STATUS_BEGIN:
			raise GsNoTransaction("can't end checking if not in a transaction")
		self._remove_devices_checking()                                                # was: _remove_devices_on_checking()
		self._transaction_status = TRANSACTION_STATUS_CKECKED

	# Persists changes to the registry by setting NEW devices to RUNNING, 
	# and removing DELETED ones.
	# The lock is released here so that other queueing concurrent threads can
	# begin() transactions in this registry.
	# Raises GsNoTransaction if begin() has not been called previously.
	def commit(self):
		if self._transaction_status < TRANSACTION_STATUS_BEGIN:
			raise GsNoTransaction("can't commit if not in a transaction")
		if self._transaction_status < TRANSACTION_STATUS_CKECKED:
			self._remove_devices_checking()                                            # was: _remove_devices_on_checking()
			self._transaction_status = TRANSACTION_STATUS_CKECKED
		self._internal_commit()
		self._registry_backup = {}
		self._tx_lock.release()
		self._transaction_status = TRANSACTION_STATUS_NONE

	def rollback(self):
		if self._transaction_status < TRANSACTION_STATUS_BEGIN:
			raise GsNoTransaction("can't rollback if not in a transaction")
		else:
			self._restore()
			self._registry_backup = {}
			self._tx_lock.release()
			self._transaction_status = TRANSACTION_STATUS_NONE

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

	# Interal adds or updates a device in the registry. 
	#
	# Existing devices are matched by path and vendor:model. That is considered
	# already a "partial match". 
	# A device that matches partially to an existing one con have had a new 
	# sub-device attached, or some other new/changed characteristics. A device 
	# is said to be a "full match" if it matches oll the (or certain) 
	# characteristics of an existing device. 
	#
	# [IMPORTANT TODO]: 
	# So far we consider "partial matches" as "full matches" until we are sure
	# that we want to detect this kind of changes in the "hardware" or
	# components of already existing devices. 
	# In general, there is much behaviour that we still have to determine 
	# regarding changes in the system, multiple devices, etc... 
	# This behaviour will have to be determined as we get experience with 
	# libwacom and the possible Wacom devices.
	# libwacom developers are mostly welcome here! :)
	#
	# Newly discovered devices that don't exist are added as NEW. 
	# Newly discovered devices that have a "partial match" are added as NEW and
	# the matched one is set to DELETED. 
	# Newly discovered devices that have a "full match" set the matched device 
	# to RUNNING.
	def _register_device(self, device):
		id = device.get_id()

		self._reg_lock.acquire()

		existing_device = self._get_device_by_id(id)
		if not existing_device:
			self._registry[id] = { 'status': self.STATUS_NEW, 'device': device }
		else:
			# Here is where we want to see if the existing record vs the device
			# in the system are exactly the same or there are some changes like
			# the device in the system has one more pen, or an airbrush is gone
			# For now we assume that they are exactly the same (just match 'id')		
			# Otherwise, if "id" matches but there were chardware changes we 
			# mark the existing record as CHANGED
			if existing_device.is_full_match(device):
				self._set_device_status(id, self.STATUS_RUNNING)
			else:
				self._set_device_status(id, self.STATUS_CHANGED)

		self._reg_lock.release()

	# Sets devices on NEW to RUNNING and and removes those on DELETED.
	def _internal_commit(self):
		self._reg_lock.acquire()

		for id in self._registry:
			if self._registry[id]['status'] == self.STATUS_NEW:
				self._registry[id]['status'] = self.STATUS_RUNNING
			elif self._registry[id]['status'] == self.STATUS_DELETED:
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

	def _remove_devices_checking(self):
		self._reg_lock.acquire()
		for id in self._registry:
			if self._registry[id]['status'] == self.STATUS_CHECKING:
				self._registry[id]['status'] = self.STATUS_DELETED
		self._reg_lock.release()

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
			if self._registry[id]["status"] == self.STATUS_NEW:
				devices.append(self._registry[id]['device'])
		self._reg_lock.release()
		return devices

	def get_devices_deleted(self):
		devices = []
		self._reg_lock.acquire()
		for id in self._registry:
			if self._registry[id]["status"] == self.STATUS_DELETED:
				devices.append(self._registry[id]['device'])
		self._reg_lock.release()
		return devices




