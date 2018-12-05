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

__all__ = ["TangoArchivingDevice"]

from PyTangoArchiving import Reader
from taurus.core.taurusdevice import TaurusDevice
from tangoarchivingvalidator import TangoArchivingDeviceNameValidator

class TangoArchivingDevice(TaurusDevice):
    """TangoArchiving device object. """
    _scheme = 'tgarch'
    _description = "A Archiving Device"

    def __init__(self, name, **kwargs):
        TaurusDevice.__init__(self, name, **kwargs)
        self._validator = TangoArchivingDeviceNameValidator()
        g = self._validator.getUriGroups(self.getFullName())
        db = g.get('arch_db', '*')
        tango_host = '%s:%s' % (g.get('host'), g.get('port'))
        self._reader = Reader(db, tango_host=tango_host, logger=self)

    def getReader(self):
        """Get the PyTangoArchiving Reader

        :return PyTangoArchiving.Reader
        """
        return self._reader

    def getAttribute(self, attrname):
        """Returns the attribute object given its name"""
        attrname = "%s/%s" % (self.getFullName(), attrname)
        return self.factory().getAttribute(attrname)

    def add_attribute(self, attribute, device, period):
        pass

    def getArchivedAttributes(self, active=False):
        """getArchivedAttributes show the names of the archived attributes

        :return: A list with the names of the current archived attributes.
        """
        return self._reader.get_attributes(active)