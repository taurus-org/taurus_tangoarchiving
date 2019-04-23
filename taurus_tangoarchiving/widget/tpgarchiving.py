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

import time
import threading
from taurus.external.qt import Qt
import pyqtgraph as pg
from taurus.qt.qtgui.application import TaurusApplication
from taurus.qt.qtgui.taurusgui import TaurusGui
from taurus.qt.qtgui.container import TaurusMainWindow
from taurus_tangoarchiving.tangoarchivingvalidator import TangoArchivingAttributeNameValidator
from taurus_tangoarchiving.tangoarchivingvalidator import str2localtime
from taurus_tangoarchiving.widget.tangoarchivingmodelchooser import TangoArchivingModelSelectorItem
from taurus.core.taurushelper import getValidatorFromName

try:
    from taurus.qt.qtgui.tpg import (TaurusPlot,
                                     DateAxisItem,
                                     TaurusPlotDataItem)
    from taurus.qt.qtgui.tpg.curvesmodel import TaurusItemConf
except ImportError:
    raise Exception('Missing dependency: taurus_pyqtgraph')


def run():
    # Simplify TaurusGui
    TaurusGui.TAURUS_MENU_ENABLED = False
    TaurusGui.TOOLS_MENU_ENABLED = False
    TaurusGui.HELP_MENU_ENABLED = False
    TaurusGui.FULLSCREEN_TOOLBAR_ENABLED = False
    TaurusGui.PANELS_MENU_ENABLED = False
    TaurusGui.APPLETS_TOOLBAR_ENABLED = False
    TaurusGui.QUICK_ACCESS_TOOLBAR_ENABLED = False

    app = TaurusApplication(app_name='tpgArchiving')
    gui = TaurusGui()
    plot = TaurusPlot()

    axis = DateAxisItem(orientation='bottom')
    plot_items = plot.getPlotItem()

    axis.attachToPlotItem(plot_items)
    # TODO (cleanup menu actions)
    if plot_items.legend is not None:
        plot_items.legend.hide()

    msi = TangoArchivingModelSelectorItem()
    # hide time stamp selector
    msi.ui.ts_checkBox.setVisible(False)
    # hide add single Y model
    msi._addSelectedAction.setVisible(False)
    msi.setModel(msi.default_model)
    # progress bar
    pb = Qt.QProgressBar()
    pb.setGeometry(0, 0, 300, 25)

    def updateProgressBar(stop=True):
        if stop is True:
            final = 1
        else:
            final = 0
        pb.setRange(0, final)

    updateProgressBar()
    ###########################################################################
    # Update t0 and t1 based on sigXRangeChanged
    ###########################################################################
    def onUpdateXViewRange():
        x, _ = plot.viewRange()
        t0, t1 = x
        t0s = str2localtime(t0)
        t1s = str2localtime(t1)
        msi.time_selector.ui.comboBox_begin.setItemText(5, t0s)
        msi.time_selector.ui.comboBox_end.setItemText(7, t1s)
        msi.time_selector.ui.comboBox_begin.setItemText(5, t0s)
        msi.time_selector.ui.comboBox_end.setItemText(7, t1s)
        msi.time_selector.ui.comboBox_begin.setCurrentIndex(5)
        msi.time_selector.ui.comboBox_end.setCurrentIndex(7)

    vb = plot.getPlotItem().getViewBox()
    vb.sigXRangeChanged.connect(onUpdateXViewRange)

    ###########################################################################
    # Legend
    ###########################################################################
    gv = Qt.QGraphicsView(Qt.QGraphicsScene())
    gv.setBackgroundBrush(Qt.QBrush(Qt.QColor('black')))
    l = pg.LegendItem(None, offset=(0, 0))
    gv.scene().addItem(l)

    def updateExternalLegend():
        for dataitem in plot_items.listDataItems():
            l.removeItem(dataitem.name())

        for dataitem in plot_items.listDataItems():
            if dataitem.name():
                l.addItem(dataitem, dataitem.name())


    ###########################################################################
    # Connect CurvesAppearanceChooser to external legend
    ###########################################################################
    from taurus_pyqtgraph.curveproperties import (CurvesAppearanceChooser,
                                                  CurveAppearanceProperties)

    def onApply(self):
        names = self.getSelectedCurveNames()
        prop = self.getShownProperties()
        # Update self.curvePropDict for selected properties
        for n in names:
            self.curvePropDict[n] = CurveAppearanceProperties.merge(
                [self.curvePropDict[n], prop],
                conflict=CurveAppearanceProperties.inConflict_update_a)
        # emit a (PyQt) signal telling what properties (first argument) need to
        # be applied to which curves (second argument)
        # self.curveAppearanceChanged.emit(prop, names)
        # return both values

        self.curvePropAdapter.setCurveProperties(self.curvePropDict, names)
        # Update legend
        updateExternalLegend()

        return prop, names

    # Override CurvesAppearanceChooser.onApply
    CurvesAppearanceChooser.onApply = onApply

    ###########################################################################
    # Helper
    ###########################################################################
    def updateAll(legend=True):
        # Update legend
        if legend is True:
            updateExternalLegend()
        # run plot auto range
        time.sleep(0.2)  # Wait till models are loading
        plot_items.getViewBox().menu.autoRange()
        # Stop progress bar
        updateProgressBar()

    ###########################################################################
    # onAddXYModel
    ###########################################################################

    def onAddXYModel(models):
        # Update progress bar
        # updateProgressBar(False)
        c = msi.cursor()
        msi.setCursor(Qt.Qt.WaitCursor)

        plot.model_chooser_tool.addModels(models)
        updateAll()
        msi.setCursor(c)

    # Connect button
    msi.modelsAdded.connect(onAddXYModel)

    ###########################################################################
    # Override TaurusGui close event
    ###########################################################################
    def closeEvent(self, event):
        try:
            self.__macroBroker.removeTemporaryPanels()
        except:
            pass
        TaurusMainWindow.closeEvent(self, event)
        for n, panel in self._TaurusGui__panels.items():
            panel.closeEvent(event)
            panel.widget().closeEvent(event)
            if not event.isAccepted():
                result = Qt.QMessageBox.question(
                    self, 'Closing error',
                    "Panel '%s' cannot be closed. Proceed closing?" % n,
                    Qt.QMessageBox.Yes | Qt.QMessageBox.No)
                if result == Qt.QMessageBox.Yes:
                    event.accept()
                else:
                    break

        for curve in plot_items.listDataItems():
            plot.removeItem(curve)
            l.removeItem(curve.name())
        gui.saveSettings()

    # Override TaurusGui close event
    TaurusGui.closeEvent = closeEvent

    ###########################################################################
    # Create tgarch tool bar
    ###########################################################################
    def _onRefresh():
        t0, t1 = msi.time_selector.getTimes()
        # Validate models
        v = TangoArchivingAttributeNameValidator()
        query = "{0};t0={1};t1={2}"
        for curve in plot.getPlotItem().listDataItems():

            if isinstance(curve, TaurusPlotDataItem):
                ymodel = curve.getModel()
                # tgarch attr
                if v.getUriGroups(ymodel).get('scheme') != 'tgarch':
                    continue
                fullname, _, _ = v.getNames(ymodel)
                bmodel, current_query = fullname.split('?')
                db = current_query.split(';')[0]
                q = query.format(db, t0, t1)
                model = "{0}?{1}".format(bmodel, q)
                xmodel = "{};ts".format(model)
                curve.setModel(None)
                curve.setXModel(None)
                curve.setModel(model)
                curve.setXModel(xmodel)
        updateAll(legend=False)

    def onRefresh():
        # Update progress bar
        updateProgressBar(False)
        t1 = threading.Thread(target=_onRefresh)
        t1.start()

    tgarchToolBar = gui.addToolBar("TgArch")
    tgarchToolBar.addAction(Qt.QIcon.fromTheme("view-refresh"),
                            "refresh tgarch curves", onRefresh)

    ###########################################################################
    # Create panels
    ###########################################################################
    gui.createPanel(plot, 'Plot')
    gui.createPanel(msi, 'Chooser')
    gui.createPanel(pb, 'Progress bar')
    gui.createPanel(gv, 'Legend')
    # Load configuration
    gui.loadSettings()
    gui.show()

    app.exec_()


if __name__ == '__main__':
    run()
