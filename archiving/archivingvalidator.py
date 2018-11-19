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

__all__ = ["ArchivingAuthorityNameValidator", "ArchivingDeviceNameValidator", 
           "ArchivingAttributeNameValidator"]

import time
import taurus
import socket
import PyTango
from fandango.functional import str2time

from taurus.core.taurusvalidator import (TaurusAttributeNameValidator,
                                         TaurusDeviceNameValidator)
from taurus.core.tango.tangovalidator import TangoAuthorityNameValidator
from taurus import tauruscustomsettings


_FIRST = getattr(tauruscustomsettings, 'ARCHIVING_FIRST_ELEM', "-1d")
_LAST = getattr(tauruscustomsettings, 'ARCHIVING_LAST_ELEM', time.time())

def str2epoch(str_time):
    try:
        v = float(str_time)
    except ValueError:
        v = time.time() + str2time(str_time)
    return v


class ArchivingAuthorityNameValidator(TangoAuthorityNameValidator):
    """Validator for Archiving authority names. Apart from the standard named
    groups (scheme, authority, path, query and fragment), the following named
    groups are created:

     - host: tango host name, without port.
     - port: port number
    """
    scheme = "archiving"

class ArchivingDeviceNameValidator(TaurusDeviceNameValidator):
    """Validator for Archiving device names. Apart from the standard named
    groups (scheme, authority, path, query and fragment), the following named
    groups are created:

     - devname: device name represent a valid scheme
     - [host] as in :class:`ArchivingAuthorityNameValidator`
     - [port] as in :class:`ArchivingAuthorityNameValidator`

    Note: brackets on the group name indicate that this group will only contain
    a string if the URI contains it.
    """
    scheme = 'archiving'
    authority = ArchivingAuthorityNameValidator.authority
    path = r''
    query = r'db(=(?P<arch_db>(hdb|hdblite|tdb|tdbpp|rad2s|rad10s|snap|hdbpp|\*)))?'
    fragment = '(?!)'

    def getNames(self, fullname, factory=None):
        """reimplemented from :class:`TaurusDeviceNameValidator`.
        """
        groups = self.getUriGroups(fullname)
        if groups is None:
            return None

        default_authority = taurus.Factory("tango").get_default_tango_host()

        if default_authority is None:
            import PyTango
            host, port = PyTango.ApiUtil.get_env_var('TANGO_HOST').split(":")
            # Get the fully qualified domain name
            host = socket.getfqdn(host)
            default_authority = "//{0}:{1}".format(host, port)

        authority = groups.get('authority')
        if authority is None:
            groups['authority'] = authority = default_authority

        complete = self.scheme + ':%(authority)s?db=%(arch_db)s' % groups

        if authority.lower() == default_authority.lower():
            normal = '?db=%(arch_db)s' % groups
        else:
            normal = '%(authority)s?db=%(arch_db)s' % groups
        short = '%(arch_db)s' % groups
        return complete, normal, short

    def getUriGroups(self, name, strict=None):
        groups = TaurusDeviceNameValidator.getUriGroups(self, name, strict)
        if groups is not None:
            if groups.get('arch_db', None) is None:
                groups['arch_db'] = '*'  # Wildcard for archiving scheme
            groups['devname'] = '?db={arch_db}'.format(**groups)
        return groups


class ArchivingAttributeNameValidator(TaurusAttributeNameValidator):
    """Validator for Archiving attribute names. Apart from the standard named
    groups (scheme, authority, path, query and fragment), the following named
    groups are created:

     - attrname: archived tango attribute name
     - devname: as in :class:`ArchivingDeviceNameValidator`
     - [host] as in :class:`ArchivingAuthorityNameValidator`
     - [port] as in :class:`ArchivingAuthorityNameValidator`

    Note: brackets on the group name indicate that this group will only contain
    a string if the URI contains it.
    """
    scheme = 'archiving'
    authority = ArchivingAuthorityNameValidator.authority
    path = r'/((?P<attrname>[^/?:#]+(/[^/?:#]+){3})|' \
           r'(?P<_shortattrname>[^/?:#]+/[^/?:#]+))'
    _dtime = '[^?#=;]+'
    _sc = '((?<=[^?#=;])(;|\?)|)'
    query = r'(({dq})?({sc}t0={t})?((;|\?)t1={t})?({sc}ts)?)?'.format(
        dq=ArchivingDeviceNameValidator.query, sc=_sc, t=_dtime)

    fragment = r'[^# ]*'

    def getNames(self, fullname, factory=None, fragment=False):
        """reimplemented from :class:`TaurusAttributeNameValidator`.
        """
        groups = self.getUriGroups(fullname)
        if groups is None:
            return None

        tango_host = PyTango.ApiUtil.get_env_var('TANGO_HOST')
        default_auth = False
        authority = groups.get('authority')
        host = groups.get('host')
        port = groups.get('port')
        if authority is None:
            default_auth = True
            groups['authority'] = '//' + tango_host
            host, port = tango_host.split(':')

        query = groups['query']
        dquery = {}
        if query is not None:
            query = query.replace('?', ';')
            groups['query'] = query
            # if a value is duplicated in the query,
            # it will be overwritten by the last value.
            for element in query.split(';'):
                if '=' in element:
                    k, v = element.split('=')
                else:
                    k = element
                    v = '*'
                dquery[k] = v

        if not 'db' in dquery:
            # db = PyTango.Database(host, port)
            # # TODO verify it is the right property
            # props = db.get_property('PyTangoArchiving', [db, 'Schemas'])
            # # Use the first scheme as default
            # dquery['db'] = props['Schemas'][0]
            dquery['db'] = '*'  # Wildcard for archiving schem

        if not 't0' in dquery:
            dquery['t0'] = _FIRST

        if not 't1' in dquery:
            dquery['t1'] = _LAST

        # From str to epoch
        dquery['t0'] = str2epoch(dquery['t0'])
        dquery['t1'] = str2epoch(dquery['t1'])

        groups['fullquery'] = "db={db};t0={t0};t1={t1}".format(**dquery)

        if 'ts' in dquery:
            groups['fullquery'] = groups['fullquery'] + ';ts'

        complete = self.scheme +\
                   ':%(authority)s/%(attrname)s?%(fullquery)s' % groups
        if default_auth:
            normal = '/%(attrname)s?%(query)s' % groups
        else:
            normal = '%(authority)s/%(attrname)s?%(query)s' % groups
        short = '%(attrname)s' % groups

        # return fragment if requested
        if fragment:
            key = groups.get('fragment', None)
            return complete, normal, short, key

        return complete, normal, short

    def getUriGroups(self, name, strict=None):
        groups = TaurusAttributeNameValidator.getUriGroups(self, name, strict)
        if groups is not None:
            if groups.get('arch_db', None) is not None:
                # add devname to the groups
                groups['devname'] = '?db={arch_db}'.format(**groups)
        return groups
