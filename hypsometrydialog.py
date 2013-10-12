# -*- coding: utf-8 -*-

"""
***************************************************************************
    hypsometrydialog.py
    ---------------------
    Date                 : October 2013
    Copyright            : (C) 2013 by Alexander Bruy
    Email                : alexannder dot bruy at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Alexander Bruy'
__date__ = 'October 2013'
__copyright__ = '(C) 2013, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from hypsometrythread import *
import hypsometryutils as utils
from ui.ui_hypsometrydialogbase import Ui_HypsometryDialog


class HypsometryDialog(QDialog, Ui_HypsometryDialog):
    def __init__(self, iface):
        QDialog.__init__(self)
        self.setupUi(self)

        self.iface = iface
        self.workThread = None

        self.btnOk = self.buttonBox.button(QDialogButtonBox.Ok)
        self.btnClose = self.buttonBox.button(QDialogButtonBox.Close)

        self.btnBrowse.clicked.connect(self.selectDirectory)

        self.manageGui()

    def manageGui(self):
        self.cmbDEM.addItems(utils.getRasterLayerNames())
        self.cmbPolygon.addItems(utils.getPolygonLayerNames())

    def selectDirectory(self):
        settings = QSettings('alexbruy', 'Hypsometry')
        lastDir = settings.value('lastDirectory', '')
        dirName = QFileDialog.getExistingDirectory(self,
                                                   self.tr('Select directory'),
                                                   lastDir,
                                                   QFileDialog.ShowDirsOnly)
        if not dirName:
            return

        self.leOutputDir.setText(dirName)
        settings.setValue("lastDirectory", os.path.dirname(dirName))

    def reject(self):
        QDialog.reject(self)

    def accept(self):
        if not self.leOutputDir.text():
            QMessageBox.warning(self,
                                self.tr('No output directory'),
                                self.tr('Output directory is not set. Please '
                                        'select directory and try again.'))
            return

        self.workThread = HypsometryThread(raster,
                                           vector,
                                           step,
                                           directory,
                                           calculatePercentage)
        self.workThread.rangeChanged.connect(self.setProgressRange)
        self.workThread.updateProgress.connect(self.updateProgress)
        self.workThread.processFinished.connect(self.processFinished)
        self.workThread.processInterrupted.connect(self.processInterrupted)

        self.btnOk.setEnabled(False)
        self.btnClose.setText(self.tr("Cancel"))
        self.buttonBox.rejected.disconnect(self.reject)
        self.btnClose.clicked.connect(self.stopProcessing)

        self.workThread.start()

    def setProgressRange(self, maxValue):
        self.progressBar.setRange(0, maxValue)

    def updateProgress(self):
        self.progressBar.setValue(self.progressBar.value() + 1)

    def processFinished(self):
        self.stopProcessing()
        self.restoreGui()

    def processInterrupted(self):
        self.restoreGui()

    def stopProcessing(self):
        if self.workThread is not None:
            self.workThread.stop()
            self.workThread = None

    def restoreGui(self):
        self.progressBar.setFormat("%p%")
        self.progressBar.setRange(0, 1)
        self.progressBar.setValue(0)

        self.buttonBox.rejected.connect(self.reject)
        self.btnClose.clicked.disconnect(self.stopProcessing)
        self.btnClose.setText(self.tr("Close"))
        self.btnOk.setEnabled(True)
