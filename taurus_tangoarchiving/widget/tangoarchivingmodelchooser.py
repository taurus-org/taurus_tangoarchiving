#!/usr/bin/env python

import re
import time
import socket
import taurus
from taurus.external.qt import Qt
from taurus.qt.qtgui.container import TaurusWidget
from taurus.qt.qtgui.panel.taurusmodellist import (TaurusModelModel,
                                                   SRC_ROLE)
from taurus.qt.qtgui.util.ui import UILoadable
from taurus_tangoarchiving.tangoarchivingvalidator import str2localtime


@UILoadable(with_ui='ui')
class TangoArchivingModelSelector(TaurusWidget):

    addModels = Qt.pyqtSignal('QStringList')
    applied = Qt.pyqtSignal() # TODO

    def __init__(self, parent=None):
        TaurusWidget.__init__(self, parent)
        # Load ui
        self.loadUi()
        self.ui.schema_comboBox.currentIndexChanged.connect(
            self.onSelectSchemeComboBox)

        self.tmodelmodel = TaurusModelModel()
        self.ui.listView.setModel(self.tmodelmodel)
        self.ui.listView.setDragDropMode(True)
        self.ui.lineEdit.editingFinished.connect(self.filter)
# TODO tree
        # self._tree = self.ui.taurusDbTreeWidget
        # self._selectables = [TaurusElementType.Attribute,
        #                      TaurusElementType.Member,
        #                      TaurusElementType.Device]
        # self._tree.getQModel().setSelectables(self._selectables)

        self.ui.pushButton.setIcon(Qt.QIcon("actions:gtk-add.svg"))
        self.ui.pushButton.clicked.connect(self.onAddSelected)
        self.ui.t0_dateTime.addItems(["-1h", "-1d", "-1w",
                                      str2localtime("-1d")])
        self.ui.t0_dateTime.setCurrentIndex(1)
        self.ui.t1_dateTime.addItems(["", "-1h", "-1d", "-1w",
                                      str2localtime(time.time())])


    def filter(self):
        filter_text = str(self.ui.lineEdit.text()).lower()
        # for item in self.tmodelmodel.items:
        for row in range(self.tmodelmodel.rowCount()):
            item = self.tmodelmodel.items[row]
            try:
                match = re.match(filter_text, str(item.getSrc()).lower())
            except:
                return

            if match is not None:
                self.ui.listView.setRowHidden(row, False)
            else:
                self.ui.listView.setRowHidden(row, True)

    def setModel(self, model):
        TaurusWidget.setModel(self, model)
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

# TODO tree
        # from PyTangoArchiving.widget.models import TaurusArchivingDatabase
        # ta_db = TaurusArchivingDatabase()
        # ta_db._reader = dev.getReader()
        # self._tree.modelObj = ta_db
        # self._tree.setModel('tango://tlarf01.cells.es:10000')

    def getSelectedModels(self):
        query = "db={0};t0={1};t1={2}"
        if self.ui.ts_checkBox.isChecked():
            query += ";ts"

        t0 = self.ui.t0_dateTime.currentText()
        t1 = self.ui.t1_dateTime.currentText()
        schema = self.ui.schema_comboBox.currentText()
        selected = self.ui.listView.selectionModel().selectedIndexes()
        models = []
        # if len(selected) == 1:
        #     idx = selected[0]
        # else:
        #     return None
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

    def onAddSelected(self):
        models = self.getSelectedModels()
        print("onAddSelected", models)
        self.addModels.emit(models)


if __name__ == '__main__':

    def print_models(models):
        print(models)

    from taurus.qt.qtgui.application import TaurusApplication
    import PyTango
    import sys
    app = TaurusApplication()

    pytango_host = PyTango.ApiUtil.get_env_var("TANGO_HOST")
    host, port = pytango_host.split(':')
    auth_name = "tgarch://{0}:{1}".format(socket.getfqdn(host), port)
        
    w = TangoArchivingModelSelector()    
    w.setModel(auth_name)

    w.addModels.connect(print_models)
    w.show()
    
    sys.exit(app.exec_())
