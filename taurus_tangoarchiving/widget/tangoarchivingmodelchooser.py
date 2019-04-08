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
import taurus
from taurus.core.tango.tangodatabase import TangoAuthority
from taurus.external.qt import Qt
from taurus.qt.qtgui.panel import TaurusModelSelectorItem
from taurus.qt.qtgui.util.ui import UILoadable
from taurus_tangoarchiving.widget.tangoarchivingtools import TangoArchivingTimeSelector


class ListModel(Qt.QStandardItemModel):

    def __init__(self, parent=None):
        Qt.QStandardItemModel.__init__(self, parent)
        self.models = []

    def addItems(self, models):

        for model in models:
            # Create an item with a caption
            item = Qt.QStandardItem(model)
            self.models.append(model)
            # Add the item to the model
            self.appendRow(item)

    def removeItems(self):
        while self.rowCount() > 0:
            self.removeRow(0)
        self.models = []


@UILoadable(with_ui='ui')
class TangoArchivingModelSelectorItem(TaurusModelSelectorItem):

    def __init__(self, parent=None):
        TaurusModelSelectorItem.__init__(self, parent)
        # Load ui
        self.loadUi()
        self.ui.schema_comboBox.currentIndexChanged.connect(
            self.onSelectSchemeComboBox)
        self.ui.active_checkBox.clicked.connect(self.onSelectSchemeComboBox)
        self.ui.ts_checkBox.clicked.connect(self.onSelectTsComboBox)
        self.listmodel = ListModel(self.ui.listView)
        self.ui.listView.setModel(self.listmodel)
        self.ui.listView.setDragDropMode(True)
        self._toolbar = Qt.QToolBar("Selector toolbar")
        self._toolbar.setOrientation(Qt.Qt.Vertical)
        self._toolbar.setIconSize(Qt.QSize(16, 16))
        self._toolbar.setFloatable(False)
        self._addSelectedAction = self._toolbar.addAction(
            Qt.QIcon.fromTheme("list-add"), "Add selected", self.onAddSelected)
        self._addSelectedActionXY = self._toolbar.addAction(
            Qt.QIcon.fromTheme("list-add"), "Add XY selected",
            self.onAddSelectedXY)
        self.ui.verticalLayout_4.addWidget(self._toolbar)
        self.ui.verticalLayout_4.setAlignment(Qt.Qt.AlignTop)
        # TODO support drag and drop from listView
        # self.ui.listView.installEventFilter(self)
        self.ui.lineEdit.textChanged.connect(self.filter)
        self.time_selector = TangoArchivingTimeSelector(self)
        self.ui.horizontalLayout_4.addWidget(self.time_selector)

    def onAddSelected(self):
        self.modelsAdded.emit(self.getSelectedModels())

    def onAddSelectedXY(self):
        self.modelsAdded.emit(self.getSelectedModels(xymodel=True))

    def setModel(self, model):
        TaurusModelSelectorItem.setModel(self, model)
        self._arch_auth = taurus.Authority(model)
        # Fill schemes
        schemas = self._arch_auth.getSchemas()
        self.ui.schema_comboBox.addItems(schemas)

    def onSelectTsComboBox(self):
        self._addSelectedActionXY.setEnabled(
            not self.ui.ts_checkBox.isChecked())

    def onSelectSchemeComboBox(self):
        schema = self.ui.schema_comboBox.currentText()
        if schema == "":
            return

        devname = "{0}?db={1}".format(self.model, schema)
        dev = taurus.Device(devname)
        active = self.ui.active_checkBox.isChecked()

        attrs = dev.getArchivedAttributes(active)
        self.listmodel.removeItems()
        self.listmodel.addItems(attrs)

    def filter(self):
        filter_text = ".*" + str(self.ui.lineEdit.text()).lower() + ".*"
        for row, attr in enumerate(self.listmodel.models):
            try:
                match = re.match(filter_text, attr)
            except Exception as e:
                print(e)
                return

            if match is not None:
                self.ui.listView.setRowHidden(row, False)
            else:
                self.ui.listView.setRowHidden(row, True)

    def getSelectedModels(self, xymodel=False):
        query = "db={0};t0={1};t1={2}"
        if self.ui.ts_checkBox.isChecked():
            query += ";ts"
        t0, t1 = self.time_selector.getTimes()
        schema = self.ui.schema_comboBox.currentText()
        selected = self.ui.listView.selectionModel().selectedIndexes()
        models = []

        for idx in selected:
            attr = self.listmodel.data(idx)
            query = query.format(schema, t0, t1)
            model = "{0}/{1}?{2}".format(self.model, attr, query)
            if xymodel is True:
                modelx = model + ";ts"
                model = (modelx, model)
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

    w.show()
    
    sys.exit(app.exec_())
