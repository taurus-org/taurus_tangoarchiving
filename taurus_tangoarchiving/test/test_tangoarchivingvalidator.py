#!/usr/bin/env python

#############################################################################
##
# This file is part of Taurus
##
# http://taurus-scada.org
##
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
# Taurus is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# Taurus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
##
# You should have received a copy of the GNU Lesser General Public License
# along with Taurus.  If not, see <http://www.gnu.org/licenses/>.
##
#############################################################################

"""Test for tangoarchivingvalidator module"""

__docformat__ = 'restructuredtext'

import time
import socket
import PyTango
import unittest
from taurus.core.test import (valid, invalid, names,
                              AbstractNameValidatorTestCase)
from taurus_tangoarchiving.tangoarchivingvalidator import (
    TangoArchivingAuthorityNameValidator,
    TangoArchivingDeviceNameValidator,
    TangoArchivingAttributeNameValidator,
    _LAST,
    str2localtime)


__PY_TANGO_HOST = PyTango.ApiUtil.get_env_var("TANGO_HOST")
host, port = __PY_TANGO_HOST.split(':')
__TANGO_HOST = "{0}:{1}".format(socket.getfqdn(host), port)


#=========================================================================
# Tests for Archiving Authority name validation
#=========================================================================
@valid(name='//foo:10000')
@valid(name='tgarch://foo:10000')
@valid(name='tgarch://foo.domain.name:10000')
@invalid(name='tgarch:foo')
@invalid(name='tgarch:foo:10000')
@invalid(name='tgarch://foo:10000/')
@invalid(name='tgarch://foo:10000#')
@invalid(name='tgarch://foo:bar')
@invalid(name='tgarch://foo:10000/foo')
@names(name='tgarch://foo:123',
       out=('tgarch://foo:123', '//foo:123', 'foo:123'))
class ArchivingAuthValidatorTestCase(AbstractNameValidatorTestCase,
                                 unittest.TestCase):
    validator = TangoArchivingAuthorityNameValidator

#=========================================================================
# Tests for Archiving Device name validation
#=========================================================================
@valid(name='tgarch:?db=hdb', groups={'arch_db': 'hdb'})
@valid(name='tgarch:?db=hdbpp', groups={'arch_db': 'hdbpp'})
@valid(name='tgarch:?db=tdb', groups={'arch_db': 'tdb'})
@valid(name='tgarch:?db=tdbpp', groups={'arch_db': 'tdbpp'})
@valid(name='tgarch:?db=rad2s', groups={'arch_db': 'rad2s'})
@valid(name='tgarch:?db=snap', groups={'arch_db': 'snap'})
@valid(name='tgarch://foo:10000?db=snap', groups={'arch_db': 'snap'})
## default db...
@valid(name='?db=hdb')
@valid(name='tgarch:?db')
@valid(name='tgarch://foo:10000?db')
##
## invalid query
@invalid(name='tgarch:?')
@invalid(name='tgarch:?foo')
##
@invalid(name='tgarch:foo')
@invalid(name='tgarch:tdbpp#')
@names(name='tgarch:?db=hdb',
       out=('tgarch://%s?db=hdb' % __TANGO_HOST, '?db=hdb', 'hdb'))
@names(name='tgarch://foo:1234?db=hdb',
       out=('tgarch://foo:1234?db=hdb', '//foo:1234?db=hdb', 'hdb'))
class ArchivingDevValidatorTestCase(AbstractNameValidatorTestCase,
                                unittest.TestCase):
    validator = TangoArchivingDeviceNameValidator

#=========================================================================
# Tests for Archiving Attribute name validation (without fragment)
#=========================================================================
@valid(name='tgarch://foo:1234/a/b/c/d?ts')
@valid(name='tgarch://foo:1234/a/b/c/d?t0=-1d;ts')
@valid(name='tgarch://foo:1234/a/b/c/d?t0=-2d;t1=-1d')
@valid(name='tgarch://foo:1234/a/b/c/d?t0=-2d;t1=-1d;ts')
@valid(name='tgarch://foo:1234/a/b/c/d?db=hdb;t0=-2d;t1=-1d;ts')
@valid(name='tgarch://foo:1234/a/b/c/d?db=rad10s;t0=2016-06-22')
@valid(name='tgarch://foo:1234/a/b/c/d?db=rad10s;t0=2016-06-22T00:00:00')
@valid(name='tgarch://foo:1234/a/b/c/d?db=rad10s;t0=2016-06-22T00')
@valid(name='tgarch://foo:1234/a/b/c/d?db=rad10s;t0=2016-06-22T00:00')



@invalid(name='tgarch://foo:1234/a/b/c/d?t1=-2d;t1=-1d')
@invalid(name='tgarch://foo:1234/a/b/c/d?t0=-2d;t0=-1d')
@valid(name='tgarch://foo:1234/a/b/c/d',
       groups={'authority': '//foo:1234', 'attrname': 'a/b/c/d'})
@valid(name='tgarch://foo:1234/a/b/c/d?db=snap',
       groups={'authority': '//foo:1234', 'arch_db': 'snap',
               'attrname': 'a/b/c/d'})
@valid(name='tgarch://foo:1234/a/b/c/d',
       groups={'authority': '//foo:1234', 'attrname': 'a/b/c/d'})
## default authority
@valid(name='tgarch:/a/b/c/d?db=hdb', groups={'arch_db': 'hdb',
                                                 'attrname': 'a/b/c/d'})
## default devname
@valid(name='tgarch://foo:1234/a/b/c/d#foo=bla',
       groups={'authority': '//foo:1234', 'attrname': 'a/b/c/d'})
## tango attribute name using a device alias e.g. mot01/position
@valid(name='tgarch://foo:1234/bar/d',
       groups={'authority': '//foo:1234', '_shortattrname': 'bar/d'})
## wrong syntax
@invalid(name='tgarch:a/b/c/d')
@invalid(name='tgarch:foo/a/b/c/d')
@invalid(name='tgarch://foo:1234/hdb/a/b/c/d')
@invalid(name='tgarch://foo:1234/bar/d?t0=-2d;t0=-1d')
@names(name='tgarch:/a/b/c/d?db=rad2s;t0=999',
       out=('tgarch://%s/a/b/c/d?db=rad2s;t0=1970-01-01T01:16:39;t1=%s' %\
            (__TANGO_HOST, str2localtime(_LAST)),
            '/a/b/c/d?db=rad2s;t0=1970-01-01T01:16:39', 'a/b/c/d'))
@names(name='tgarch://foo:1234/a/b/c/d?db=tdb;t0=1542681831',
       out=('tgarch://foo:1234/a/b/c/d?db=tdb;t0=2018-11-20T03:43:51;t1=%s' % str2localtime(_LAST),
            '//foo:1234/a/b/c/d?db=tdb;t0=2018-11-20T03:43:51', 'a/b/c/d'))
@names(name='tgarch:/a/b/c/d?db=tdb?t0=1542681831.7#label',
       out=('tgarch://%s/a/b/c/d?db=tdb;t0=2018-11-20T03:43:51;t1=%s' %\
            (__TANGO_HOST, str2localtime(_LAST)),
            '/a/b/c/d?db=tdb;t0=2018-11-20T03:43:51', 'a/b/c/d', 'label'))
class ArchivingAttrValidatorTestCase(AbstractNameValidatorTestCase,
                                 unittest.TestCase):
    validator = TangoArchivingAttributeNameValidator
