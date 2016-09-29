#!/usr/bin/env python
#############################################################################
##
## This file is part of Taurus
## 
## http://taurus-scada.org
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
## 
## Taurus is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Taurus is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Taurus.  If not, see <http://www.gnu.org/licenses/>.
##
#############################################################################

__all__ = ['ArchivingFactory']


from taurus.core.taurusbasetypes import TaurusElementType
from archivingattribute import ArchivingAttribute
from archivingauthority import ArchivingAuthority
from archivingdevice import ArchivingDevice
from taurus.core.taurusexception import TaurusException
from taurus.core.util.log import Logger
from taurus.core.util.singleton import Singleton
from taurus.core.taurusfactory import TaurusFactory

from taurus.core.tauruspollingtimer import TaurusPollingTimer

try:
    import PyTangoArchiving
except ImportError:
    PyTangoArchiving = None

class ArchivingFactory(Singleton, TaurusFactory, Logger):
    """
    A Singleton class that provides Archiving related objects.
    """
    schemes = ("archiving",)

    elementTypesMap = {TaurusElementType.Authority: ArchivingAuthority,
                       TaurusElementType.Device: ArchivingDevice,
                       TaurusElementType.Attribute: ArchivingAttribute
                       }

    def __init__(self):
        """ Initialization. Nothing to be done here for now."""
        pass

    def init(self, *args, **kwargs):
        """Singleton instance initialization."""
        if PyTangoArchiving is None:
            raise TaurusException('PyTangoArchiving is not available')
        name = self.__class__.__name__
        self.call__init__(Logger, name)
        self.call__init__(TaurusFactory)
        self._devs = {}
        self._attrs = {}
        self._auth = None

    def getAuthority(self, auth_name):
        """Obtain the ArchivingDatabase object.
        :return: (ArchivingAuthority)
        """
        if self._auth is None:
            # TODO we accept default authority?
            # if auth_name is None:
            #     auth_name = PyTango
            v = self.getAuthorityNameValidator()
            if not v.isValid(auth_name):
                raise TaurusException(
                    "Invalid Archiving authority name %s" % auth_name)
            self._auth = ArchivingAuthority(auth_name)
        return self._auth

    def getDevice(self, dev_name):
        """Obtain the object corresponding to the given device name. If the 
        corresponding device already exists, the existing instance is returned. 
        Otherwise a new instance is stored and returned.
           
        :param dev_name: (str) the device name string. See
                         :mod:`taurus.core.archiving` for valid device names
        
        :return: (ArchivingDevice)
         
        @throws TaurusException if the given name is invalid.
        """
        d = self._devs.get(dev_name, None)
        if d is None:
            # find the full_name and see if we already know it
            validator = self.getDeviceNameValidator()
            names = validator.getNames(dev_name)
            if names is None:
                raise TaurusException("Invalid archiving device name %s" %
                                      dev_name)
            fullname, _, _ = names
            d = self._devs.get(fullname, None)
            # if we do not know it, create the dev and store it in cache
            if d is None:
                groups = validator.getUriGroups(dev_name)
                # Get authority
                auth_name = groups.get('authority')
                authority = self.getAuthority(auth_name)
                # Create Device
                d = ArchivingDevice(fullname, parent=authority,
                                    storeCallback=self._storeDev)
        return d
        
    def getAttribute(self, attr_name):
        """Obtain the object corresponding to the given attribute name. If the
        corresponding attribute already exists, the existing instance is
        returned. Otherwise a new instance is stored and returned. The evaluator
        device associated to this attribute will also be created if necessary.

        :param attr_name: (str) the attribute name string. See
                          :mod:`taurus.core.archiving` for valid attribute
                          names

        :return: (ArchivingAttribute)

        @throws TaurusException if the given name is invalid.
        """
        a = self._attrs.get(attr_name, None)
        if a is None:
            validator = self.getAttributeNameValidator()
            names = validator.getNames(attr_name)
            if names is None:
                raise TaurusException(
                    "Invalid Archiving attribute name %s" % attr_name)
            fullname, _, _ = names
            a = self._attrs.get(fullname, None)
            # if we do not know it, create the dev and store it in cache
            if a is None:
                group = validator.getUriGroups(attr_name)
                dev_name = 'archiving:%s/%s' % (group.get("authority"),
                                                group.get("devname"))
                device = self.getDevice(dev_name)
                a = ArchivingAttribute(attr_name, device,
                                       storeCallback=self._storeAttr)
        return a

    def getAuthorityNameValidator(self):
        """Return ArchivingDatabaseNameValidator"""
        import archivingvalidator
        return archivingvalidator.ArchivingAuthorityNameValidator()
                 
    def getDeviceNameValidator(self):
        """Return ArchivingDeviceNameValidator"""
        import archivingvalidator
        return archivingvalidator.ArchivingDeviceNameValidator()

    def getAttributeNameValidator(self):
        """Return ArchivingAttributeNameValidator"""
        import archivingvalidator
        return archivingvalidator.ArchivingAttributeNameValidator()

    def _storeDev(self, dev):
        name = dev.getFullName()
        exists = self._devs.get(name, None)
        if exists is None:
            self._devs[name] = dev

    def _storeAttr(self, attr):
        name = attr.getFullName()
        exists = self._attrs.get(name, None)
        if exists is None:
            self._attrs[name] = attr

    #---------------------------------------------------------------------------
    # TODO
    def addAttributeToPolling(self, attribute, period, unsubscribe_evts=False):
        """Activates the polling (client side) for the given attribute with the
           given period (seconds).

           :param attribute: (taurus.core.tango.TangoAttribute) attribute name.
           :param period: (float) polling period (in seconds)
           :param unsubscribe_evts: (bool) whether or not to unsubscribe from events
        """
        tmr = self.polling_timers.get(period, TaurusPollingTimer(period))
        self.polling_timers[period] = tmr
        tmr.addAttribute(attribute, self.isPollingEnabled())

    def removeAttributeFromPolling(self, attribute):
        """Deactivate the polling (client side) for the given attribute. If the
           polling of the attribute was not previously enabled, nothing happens.

           :param attribute: (str) attribute name.
        """
        p = None
        for period, timer in self.polling_timers.iteritems():
            if timer.containsAttribute(attribute):
                timer.removeAttribute(attribute)
                if timer.getAttributeCount() == 0:
                    p = period
                break
        if p:
            del self.polling_timers[period]