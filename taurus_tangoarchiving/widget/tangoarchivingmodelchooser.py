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

import time
import taurus
from taurus.core.tango.tangodatabase import TangoAuthority
from taurus.external.qt import Qt, QtCore
from taurus.qt.qtgui.panel import TaurusModelSelectorItem
from taurus.qt.qtgui.panel.taurusmodellist import (TaurusModelModel,
                                                   SRC_ROLE)
from taurus.qt.qtgui.util.ui import UILoadable
from taurus_tangoarchiving.tangoarchivingvalidator import str2localtime


@UILoadable(with_ui='ui')
class TangoArchivingModelSelectorItem(TaurusModelSelectorItem):

    def __init__(self, parent=None):
        TaurusModelSelectorItem.__init__(self, parent)
        # Load ui
        self.loadUi()
        self.ui.schema_comboBox.currentIndexChanged.connect(
            self.onSelectSchemeComboBox)

        self.tmodelmodel = TaurusModelModel()
        self.ui.listView.setModel(self.tmodelmodel)
        self.ui.listView.setDragDropMode(True)

        self._toolbar = Qt.QToolBar("TangoSelector toolbar")
        self._toolbar.setIconSize(Qt.QSize(16, 16))
        self._toolbar.setFloatable(False)
        self._addSelectedAction = self._toolbar.addAction(
            Qt.QIcon.fromTheme("list-add"), "Add selected", self.onAddSelected)
        self.ui.verticalLayout_4.addWidget(self._toolbar)
        self.ui.verticalLayout_4.setAlignment(QtCore.Qt.AlignTop)

        # TODO support drag and drop from listView
        # self.ui.listView.installEventFilter(self)
        self.ui.lineEdit.editingFinished.connect(self.filter)
        self.ui.t0_dateTime.addItems(["-1h", "-1d", "-1w",
                                      str2localtime("-1d")])
        self.ui.t0_dateTime.setCurrentIndex(1)
        self.ui.t1_dateTime.addItems(["", "-1h", "-1d", "-1w",
                                      str2localtime(time.time())])

    def onAddSelected(self):
        self.modelsAdded.emit(self.getSelectedModels())

    def setModel(self, model):
        TaurusModelSelectorItem.setModel(self, model)
        self._arch_auth = taurus.Authority(model)
        # Fill schemes
        schemas = self._arch_auth.getSchemas()
        self.ui.schema_comboBox.addItems(schemas)

    def onSelectSchemeComboBox(self):
        schema = self.ui.schema_comboBox.currentText()
        if schema == "":
            return

        devname = "{0}?db={1}".format(self.model, schema)
        dev = taurus.Device(devname)
        active = self.ui.active_checkBox.isChecked()

        attrs = dev.getArchivedAttributes(active)
        self.tmodelmodel.clearAll()
        self.tmodelmodel.insertItems(0, attrs)
        self.tmodelmodel.installEventFilter(self)

    def getSelectedModels(self):
        query = "db={0};t0={1};t1={2}"
        if self.ui.ts_checkBox.isChecked():
            query += ";ts"

        t0 = self.ui.t0_dateTime.currentText()
        t1 = self.ui.t1_dateTime.currentText()
        schema = self.ui.schema_comboBox.currentText()
        selected = self.ui.listView.selectionModel().selectedIndexes()
        models = []

        for idx in selected:
            attr = self.tmodelmodel.data(idx, role=SRC_ROLE)

            if len(t0) == 0:
                return None

            if len(t1) == 0:
                t1 = time.time()

            try:
                t0 = str2localtime(t0)
            except:
                raise Exception("Invalid t0 time")

            try:
                t1 = str2localtime(t1)
            except:
                raise Exception("Invalid t1 time")

            query = query.format(schema, t0, t1)
            model = "{0}/{1}?{2}".format(self.model, attr, query)
            models.append(model)
        return models

    def _get_default_model(self):
        if self._default_model is None:
            tango_host = TangoAuthority.get_default_tango_host()
            self._default_model = "tgarch://{0}".format(tango_host)
        return self._default_model

    default_model = property(fget=_get_default_model,
                             fset=TaurusModelSelectorItem._set_default_model)


if __name__ == '__main__':
    def print_models(models):
        print(models)

    from taurus.qt.qtgui.application import TaurusApplication
    import sys
    app = TaurusApplication()
    w = TangoArchivingModelSelectorItem()
    w.setModel(w.default_model)

    w.addModels.connect(print_models)
    w.show()
    
    sys.exit(app.exec_())