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
import datetime

from taurus.external.pint import Q_
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
        self._reader = self.getParentObj().getReader()
        self._validator = ArchivingAttributeNameValidator()
        groups = self._validator.getUriGroups(name)
        self._star_date = self._EPOCH
        self._end_date = None
        _time = groups.get('query', None)
        if _time is not None and _time.startswith('time='):
            _time = _time[5:]
            dates = _time.split(',')
            self._star_date = dates[0]
            if len(dates) == 2:
                self._end_date = dates[1]
        self._value = TaurusAttrValue()
        # TODO: do it from reader
        self.type = DataType.Float
        self.data_format = DataFormat._1D
        # set the label
        self._tg_attr_name = groups.get('attrname')
        self._label = self._tg_attr_name + '(archiving)'
        # activate polling
        # self._activatePolling() #TODO ?

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Necessary to overwrite
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    def encode(self, value):
        return value

    def decode(self, attr_value):
        return attr_value

    def write(self, value, with_read=True):
        raise TaurusException('Archiving attributes are read-only')

    def read(self, cache=True):
        data = self._reader.get_attribute_values(self._tg_attr_name,
                                                 self._star_date,
                                                 self._end_date, decimate=True)
        if len(data) > 0:
            times, values = zip(*data)
            self._value.rvalue = Q_(values)
            self._value.time = times
            # TODO
            # if self._end_date is not None:
            #     self._deactivatePolling()
        else:
            self._value.rvalue = []
            self._value.time = TaurusTimeVal().now() #TODO ?

        return self._value

    def poll(self):
        v = self.read(cache=False)
        if len(v.rvalue) > 0:
            self.fireEvent(TaurusEventType.Periodic, v)
        # i = datetime.datetime.now()
        # self._star_date = "%s" % i

    def _subscribeEvents(self):
        pass

    def _unsubscribeEvents(self):
        pass

    def isUsingEvents(self):
        return False
