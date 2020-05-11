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

__all__ = ["TangoArchivingAttribute"]

import re
import time
import numpy as np
import PyTangoArchiving as pta

from taurus.core.units import Q_
from taurus.core.taurusattribute import TaurusAttribute
from taurus.core.taurusexception import TaurusException
from taurus.core.taurusbasetypes import (TaurusEventType,
                                         TaurusAttrValue,
                                         TaurusTimeVal,
                                         DataFormat, DataType)
from tangoarchivingvalidator import TangoArchivingAttributeNameValidator



class TangoArchivingAttribute(TaurusAttribute):
    '''
    A :class:`TaurusAttribute` that gives access to a TangoArchiving Process
    Variable.
    

    .. warning:: In most cases this class should not be instantiated directly.
                 Instead it should be done via the :meth:`ArchivingFactory.getAttribute`
    '''

    _scheme = 'tgarch'

    def __init__(self, name, parent, **kwargs):
        self.__enable_polling = False
        self.call__init__(TaurusAttribute, name, parent)
        self.parent = parent
        self._validator = TangoArchivingAttributeNameValidator()
        groups = self._validator.getUriGroups(name)
        self._start_date = None
        self._end_date = None
        self._return_timestamps = False
        arch_label = "(archiving)"

        self._query = groups.get('query', None)
        if self._query is not None:
            for query_elem in self._query.split(';'):
                if 't0=' in query_elem:
                    self._start_date = query_elem[3:]
                if 't1=' in query_elem:
                    self._end_date = query_elem[3:]
                    if self._end_date == 'now':
                        self._end_date = time.time()
                if 'ts' in query_elem:
                    self._return_timestamps = True
                    arch_label = "(archiving ts)"

        self._arch_values = TaurusAttrValue()
        self._arch_timestamps = TaurusAttrValue()
        # set the label
        self._tg_attr_name = groups.get('attrname')
        self._label = "{} {}".format(self._tg_attr_name, arch_label)

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
        if self._return_timestamps is True:
            partial_query += ";ts"
        fullname = name + partial_query
        return fullname

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Necessary to overwrite
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    def encode(self, value):
        value_dimension = len(np.shape(value))
        self.data_format = DataFormat(value_dimension)
        if self.isNumeric():
            v = Q_(np.array(value, dtype=np.float))
        else:
            v = np.array(value)
        return v

    def decode(self, attr_value):
        return attr_value

    def write(self, value, with_read=True):
        raise TaurusException('Archiving attributes are read-only')

    def read(self, cache=True):
        if not cache:
            self.warning("Ignoring cache=False in read() call of tgarch attr")

        if self._return_timestamps is True:
            return self._arch_timestamps
        else:
            return self._arch_values

    def _read(self):
        reader = self.parent.getReader()
        data = reader.get_attribute_values(self._tg_attr_name,
                                    self._start_date,
                                    self._end_date,
                                    decimate=True)
        t = TaurusTimeVal().now()
        self.type = self.getType()
        if len(data) > 0:
            times, values = zip(*data)
            self._arch_values.rvalue = self.encode(values)
            self._arch_timestamps.rvalue = Q_(times, 's')
        else:
            self._arch_values.rvalue = np.array([])
            self._arch_timestamps.rvalue = np.array([])
        self._arch_values.time = t
        self._arch_timestamps.time = t

        if self._return_timestamps is True:
            v = self._arch_timestamps
        else:
            v = self._arch_values

        return v

    def getType(self, cache=True):
        if self.type is None:
            reader = self.parent.getReader()
            api = pta.api(reader.db_name)
            try:
                _, _, pta_type = api.get_attr_id_type_table(self._tg_attr_name)
            except:
                pta_type = 'float'
            # TODO  AttributeError("'ArchivingAPI' object has no attribute 'get_attr_id_type_table'
            if re.match('.*short.*|.*long.*', pta_type):
                self.type = DataType.Integer
            elif re.match('.*state.*', pta_type):
                self.type = DataType.DevState
            elif re.match('.*float.*|.*double.*', pta_type):
                self.type = DataType.Float
            elif re.match('.*boolean.*', pta_type):
                self.type = DataType.Boolean
            elif re.match('.*string.*', pta_type):
                self.type = DataType.String
            elif re.match('.*uchar.*', pta_type):
                self.type = DataType.Bytes
            elif re.match('.*encoded.*', pta_type):
                self.type = DataType.DevEncoded
            elif re.match('.*enum.*', pta_type):
                self.type = DataType.Object

        return self.type

    def addListener(self, listener):
        added = TaurusAttribute.addListener(self, listener)
        if added:
            v = self.read()
            self.fireEvent(TaurusEventType.Periodic, v, listeners=[listener])

        return added

    def poll(self):
        raise TaurusException('Archiving attributes do not support polling')

    def isUsingEvents(self):
        return False

