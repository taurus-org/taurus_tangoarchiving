=====================================
Notes on integration with ctarchiving
=====================================

To launch tpgarchiving:
 
  python taurus_tangoarchiving/widget/tpgarchiving.py 

Trend Widget API on ctarchiving
-------------------------------

.. code::

    plot = TaurusPlot()
    plot.setBackgroundBrush(Qt.QColor('white'))
    axis = DateAxisItem(orientation='bottom')
    plot_items = plot.getPlotItem()

    axis.attachToPlotItem(plot_items)
    # TODO (cleanup menu actions)
    if plot_items.legend is not None:
        plot_items.legend.hide()
        
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
    gv.setBackgroundBrush(Qt.QBrush(Qt.QColor('white')))
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

    def onAddXYModel(models=None):
        # Update progress bar
        # updateProgressBar(False)
        print('onAddXYModel(%s)'%models)
        if not isSequenceType(models):
            print('Overriding models ...')
            models = msi.getSelectedModels()
            
        c = msi.cursor()
        msi.setCursor(Qt.Qt.WaitCursor)
        current = plot._model_chooser_tool.getModelNames()
        print('current: %s' % str(current))
        models = [m for m in models if m not in current]
        print('new models: %s' % str(models))
        plot.addModels(models)
        updateAll()
        msi.setCursor(c)

    # Connect button
    msi.modelsAdded.connect(onAddXYModel)
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
        
PyQtGraph API on tpgarchiving
-----------------------------

.. code::

            from taurus.qt.qtgui.plot import TaurusTrend
            from PyTangoArchiving.widget.trend import ArchivingTrend,ArchivingTrendWidget
            self.trend = ArchivingTrendWidget() #TaurusArchivingTrend()
            self.trend.setUseArchiving(True)
            self.trend.showLegend(True)
