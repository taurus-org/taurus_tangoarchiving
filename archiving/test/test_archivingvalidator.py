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

"""Test for taurus.core.archiving.test.test_archivingvalidator..."""

__docformat__ = 'restructuredtext'

import socket
import PyTango
import unittest
from taurus.core.test import (valid, invalid, names,
                              AbstractNameValidatorTestCase)
from archiving.archivingvalidator import (ArchivingAuthorityNameValidator,
                                          ArchivingDeviceNameValidator,
                                          ArchivingAttributeNameValidator)
from taurus import tauruscustomsettings


__PY_TANGO_HOST = PyTango.ApiUtil.get_env_var("TANGO_HOST")
host, port = __PY_TANGO_HOST.split(':')
__TANGO_HOST = "{0}:{1}".format(socket.getfqdn(host), port)

_FIRST = getattr(tauruscustomsettings, 'ARCHIVING_FIRST_ELEM', "-1d")
_LAST = getattr(tauruscustomsettings, 'ARCHIVING_LAST_ELEM', "now")

#=========================================================================
# Tests for Archiving Authority name validation
#=========================================================================
@valid(name='archiving://foo:10000')
@valid(name='archiving://foo.domain.name:10000')
@invalid(name='archiving:foo')
@invalid(name='archiving:foo:10000')
@invalid(name='archiving://foo:10000/')
@invalid(name='archiving://foo:10000#')
@invalid(name='archiving://foo:bar')
@invalid(name='archiving://foo:10000/foo')
@names(name='archiving://foo:123',
       out=('archiving://foo:123', '//foo:123', 'foo:123'))
class ArchivingAuthValidatorTestCase(AbstractNameValidatorTestCase,
                                 unittest.TestCase):
    validator = ArchivingAuthorityNameValidator

#=========================================================================
# Tests for Archiving Device name validation
#=========================================================================
@valid(name='archiving:?db=hdb', groups={'devname': 'hdb'})
@valid(name='archiving:?db=tdb', groups={'devname': 'tdb'})
@valid(name='archiving:?db=tdbpp', groups={'devname': 'tdbpp'})
@valid(name='archiving:?db=rad2s', groups={'devname': 'rad2s'})
@valid(name='archiving:?db=snap', groups={'devname': 'snap'})
@valid(name='archiving://foo:10000?db=snap', groups={'devname': 'snap'})
## default db...
@valid(name='archiving:?db')
@valid(name='archiving://foo:10000?db')
##
## invalid query
@invalid(name='archiving:?')
@invalid(name='archiving:?foo')
##
## invalid db foo
@invalid(name='archiving:?db=foo')
##
@invalid(name='archiving:foo')
@invalid(name='archiving:tdbpp#')
@names(name='archiving:?db=hdb',
       out=('archiving://%s?db=hdb' % __TANGO_HOST, '?db=hdb', 'hdb'))
@names(name='archiving://foo:1234?db=hdb',
       out=('archiving://foo:1234?db=hdb', '//foo:1234?db=hdb', 'hdb'))
class ArchivingDevValidatorTestCase(AbstractNameValidatorTestCase,
                                unittest.TestCase):
    validator = ArchivingDeviceNameValidator

#=========================================================================
# Tests for Archiving Attribute name validation (without fragment)
#=========================================================================
@valid(name='archiving://foo:1234/a/b/c/d',
       groups={'authority': '//foo:1234', 'attrname': 'a/b/c/d'})
@valid(name='archiving://foo:1234/a/b/c/d?db=snap',
       groups={'authority': '//foo:1234', 'devname': 'snap',
               'attrname': 'a/b/c/d'})
@valid(name='archiving://foo:1234/a/b/c/d',
       groups={'authority': '//foo:1234', 'attrname': 'a/b/c/d'})
## default authority
@valid(name='archiving:/a/b/c/d?db=hdb', groups={'devname': 'hdb',
                                                 'attrname': 'a/b/c/d'})
## default devname
@valid(name='archiving://foo:1234/a/b/c/d#foo=bla',
       groups={'authority': '//foo:1234', 'attrname': 'a/b/c/d'})
## tango attribute name using a device alias e.g. mot01/position
@valid(name='archiving://foo:1234/bar/d',
       groups={'authority': '//foo:1234', '_shortattrname': 'bar/d'})
## wrong syntax
@invalid(name='archiving:a/b/c/d')
@invalid(name='archiving:foo/a/b/c/d')
@invalid(name='archiving://foo:1234/hdb/a/b/c/d')
# The validator does not check queries with duplicated variables
@valid(name='archiving://foo:1234/bar/d?t0=-d1;t0=-d2')
#
@names(name='archiving://foo:1234/a/b/c/d?db=rad2s',
       out=('archiving://foo:1234/a/b/c/d?db=rad2s;t0=%s;t1=%s' %\
            (_FIRST, _LAST), '//foo:1234/a/b/c/d?db=rad2s',
            'a/b/c/d'))
@names(name='archiving:/a/b/c/d?db=rad2s',
       out=('archiving://%s/a/b/c/d?db=rad2s;t0=%s;t1=%s' %\
            (__TANGO_HOST, _FIRST, _LAST),
            '/a/b/c/d?db=rad2s', 'a/b/c/d'))
@names(name='archiving://foo:1234/a/b/c/d?db=rad10s;t0=2016-06-22T00:00:00',
       out=('archiving://foo:1234/a/b/c/d?db=rad10s;' +
            't0=2016-06-22T00:00:00;t1=%s' % _LAST,
            '//foo:1234/a/b/c/d?db=rad10s;t0=2016-06-22T00:00:00',
            'a/b/c/d'))
@names(name='archiving://foo:1234/a/b/c/d?db=hdblite' +
            '?t0=2016/06/21T00:00:00?t1=2016/06/22T00:00:00',
       out=('archiving://foo:1234/a/b/c/d?db=hdblite;' +
            't0=2016/06/21T00:00:00;t1=2016/06/22T00:00:00',
            '//foo:1234/a/b/c/d?db=hdblite;t0=2016/06/21T00:00:00;' +
            't1=2016/06/22T00:00:00',
            'a/b/c/d'))
@names(name='archiving://foo:1234/a/b/c/d?db=tdb;t0=-0.5d',
       out=('archiving://foo:1234/a/b/c/d?db=tdb;t0=-0.5d;t1=%s' % _LAST,
            '//foo:1234/a/b/c/d?db=tdb;t0=-0.5d', 'a/b/c/d'))

@names(name='archiving:/a/b/c/d?db=tdb?t0=-0.5d#label',
       out=('archiving://%s/a/b/c/d?db=tdb;t0=-0.5d;t1=%s' %\
            (__TANGO_HOST, _LAST),
            '/a/b/c/d?db=tdb;t0=-0.5d', 'a/b/c/d', 'label'))
class ArchivingAttrValidatorTestCase(AbstractNameValidatorTestCase,
                                 unittest.TestCase):
    validator = ArchivingAttributeNameValidator
