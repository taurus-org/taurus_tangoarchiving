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

__all__ = ["TangoArchivingAuthority"]

import taurus
import socket
import PyTango
from taurus.core.taurusauthority import TaurusAuthority
from taurus.core.taurusexception import TaurusException
from tangoarchivingvalidator import TangoArchivingAuthorityNameValidator


class TangoArchivingAuthority(TaurusAuthority):
    '''
    TangoArchiving authority class for Archiving
    '''

    _scheme = 'tgarch'

    def __init__(self, name=None, parent=None):
        if name is None:
            t_f = taurus.Factory('tango')
            t_default_authority = t_f.get_default_tango_host()

            if t_default_authority is None:
                pytango_host = PyTango.ApiUtil.get_env_var("TANGO_HOST")
                host, port = pytango_host.split(':')
                t_default_authority = "//{0}:{1}".format(socket.getfqdn(host),
                                                         port)

            name = '%s:%s' %(self._scheme, t_default_authority)

        TaurusAuthority.__init__(self, name, parent)
        v = TangoArchivingAuthorityNameValidator()
        groups = v.getUriGroups(name)
        if groups is None:
            raise TaurusException('Invalid name %s' % name)
        host = groups.get('host')
        port = groups.get('port')
        try:
            self._tangodb = PyTango.Database(host, port)
        except PyTango.DevFailed:
            raise TaurusException('Can not connect to the tango database')

    def getArchivingProperties(self):
        # The archiving database configuration is defined in the tango database
        # as free property.
        props = self._tangodb.get_property('PyTangoArchiving',
                                           [self._tangodb, 'DbConfig'])
        return props

    def getSchemas(self):
        """ Returns a list of configured archiving schemas"""
        # The archiving database configuration is defined in the tango database
        # as free property.
        props = self._tangodb.get_property('PyTangoArchiving',
                                           [self._tangodb, 'Schemas'])
        schemas = props.get('Schemas', [])
        if len(schemas) != 0:
            schemas.append('*')
        return schemas
