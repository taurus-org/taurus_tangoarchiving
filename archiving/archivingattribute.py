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

__all__ = ["ArchivingAttribute"]

import time
import numpy as np

from taurus.core.units import Q_
from taurus.core.taurusattribute import TaurusAttribute
from taurus.core.taurusexception import TaurusException
from taurus.core.taurusbasetypes import (TaurusEventType,
                                         TaurusAttrValue,
                                         TaurusTimeVal,
                                         DataFormat, DataType)
from archivingvalidator import ArchivingAttributeNameValidator



class ArchivingAttribute(TaurusAttribute):
    '''
    A :class:`TaurusAttribute` that gives access to an Archiving Process Variable.
    
    .. seealso:: :mod:`taurus.core.archiving` 
    
    .. warning:: In most cases this class should not be instantiated directly.
                 Instead it should be done via the :meth:`ArchivingFactory.getAttribute`
    '''

    _scheme = 'archiving'
     # Archiving reading limited to last 10 years. #TODO verify
    _EPOCH = time.time()-10*365*24*3600

    def __init__(self, name, parent, **kwargs):
        self.call__init__(TaurusAttribute, name, parent)
        self.parent = parent
        self._validator = ArchivingAttributeNameValidator()
        groups = self._validator.getUriGroups(name)
        self._star_date = self._EPOCH
        self._end_date = None
        self.return_timestamps = False
        arch_label = "(archiving)"

        self._query = groups.get('query', None)
        if self._query is not None:
            for query_elem in self._query.split(';'):
                if 't0=' in query_elem:
                    self._star_date = query_elem[3:]
                if 't1=' in query_elem:
                    self._end_date = query_elem[3:]
                    if self._end_date == 'now':
                        self._end_date = time.time()
                if 'ts' in  query_elem:
                    self.return_timestamps = True
                    arch_label = "(archiving ts)"

        self._arch_values = TaurusAttrValue()
        self._arch_timestamps = TaurusAttrValue()
        # set the label
        self._tg_attr_name = groups.get('attrname')
        self._label = "{} {}".format(self._tg_attr_name, arch_label)

        wantpolling = not self.isUsingEvents()
        haspolling = self.isPollingEnabled()
        if wantpolling:
            self._activatePolling()
        elif haspolling and not wantpolling:
            self.disablePolling()

    def getComplementaryUri(self):
        """ Returns the attribute complementary URI (fullname)"""
        fullname = self.fullname
        complementary = None
        if self._query is not None:
            if 'ts' in self._query:
                complementary = fullname.replace(';ts', '')
            else:
                complementary = fullname + ';ts'
        return complementary

    def getUriTemplate(self):
        """ Returns a URI template (fullname)"""
        fullname = self.fullname
        name = fullname.split(';')[0]
        partial_query = "{;t0={0};t1={1}}"
        if self.return_timestamps is True:
            partial_query += ";ts"
        fullname = name + partial_query
        return fullname

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Necessary to overwrite
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    def encode(self, value):
        v = np.array(value)
        if len(v.shape) == 1:
            self.data_format = DataFormat._1D
        elif len(v.shape) == 2:
            self.data_format = DataFormat._2D
        else:
            raise Exception('Data structure is not supported')

        if isinstance(v[0], (int, float)):
            v = Q_(v)
        return v

    def decode(self, attr_value):
        return attr_value

    def write(self, value, with_read=True):
        raise TaurusException('Archiving attributes are read-only')

    def read(self, cache=True):
        if cache and self._arch_values.rvalue is not None:
            if self.return_timestamps is True:
                return self._arch_timestamps
            else:
                return self._arch_values

        reader = self.parent.getReader()

        data = reader.get_attribute_values(self._tg_attr_name, self._star_date,
                                           self._end_date, decimate=True)
        if len(data) > 0:
            times, values = zip(*data)
            self._arch_values.rvalue = self.encode(values)
            self._arch_timestamps.rvalue = Q_(times, 's')
        else:
            self._arch_values.rvalue = []
            self._arch_timestamps.rvalue = []
        self._arch_values.time = TaurusTimeVal().now()
        self._arch_timestamps.time = TaurusTimeVal().now()

        if self.return_timestamps is True:
            return self._arch_timestamps
        else:
            return self._arch_values

    def poll(self):
        v = self.read(cache=True)
        self.fireEvent(TaurusEventType.Periodic, v)

    def _subscribeEvents(self):
        pass

    def _unsubscribeEvents(self):
        pass

    def isUsingEvents(self):
        return False
