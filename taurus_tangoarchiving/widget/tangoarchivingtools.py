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

import re
import time
from taurus.external.qt import Qt
from taurus.qt.qtgui.util.ui import UILoadable
from fandango.functional import str2time, clmatch, clsearch
from taurus_tangoarchiving.tangoarchivingvalidator import str2localtime

@UILoadable(with_ui='ui')
class TangoArchivingTimeSelector(Qt.QWidget):

    _ts_re = re.compile(('^(\d{4})-(\d{1,2})-(\d{1,2})'
                         + '(T\d{1,2}(:\d{1,2}((:\d{1,2})?))?)?'))

    def __init__(self, parent=None):
        Qt.QWidget.__init__(self, parent)
        self.loadUi()
        self.ui.comboBox_begin.addItem(str2localtime("-1d"))
        self.ui.comboBox_end.addItem(str2localtime(time.time()))

    def getTimes(self):
        t0 = str2localtime(self.ui.comboBox_begin.currentText())
        t1s = self.ui.comboBox_end.currentText()
        # if not absolute time
        if self._ts_re.match(t1s) is None:
            t1s = t1s.replace('now', '{}'.format(time.time() - str2time(t0)))
            t1s = str2time(t0) + str2time(t1s)
        t1 = str2localtime(t1s)
        return t0, t1


if __name__ == '__main__':

    from taurus.qt.qtgui.application import TaurusApplication
    import sys
    app = TaurusApplication()
    button = Qt.QPushButton("Press me")
    w = TangoArchivingTimeSelector()
    def p_getTimes():
        print(w.getTimes())
    button.pressed.connect(p_getTimes)
    w.ui.horizontalLayout.addWidget(button)
    w.show()
    
    sys.exit(app.exec_())
