# -*- coding: utf-8 -*-

"""
***************************************************************************
    hypsometry.py
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

import hypdsometrydialog
import aboutdialog

import resources_rc


class HypsometryPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        self.qgsVersion = unicode(QGis.QGIS_VERSION_INT)

        userPluginPath = QFileInfo(
                QgsApplication.qgisUserDbFilePath()).path() \
                + '/python/plugins/hypsometry'
        systemPluginPath = QgsApplication.prefixPath() \
                + '/python/plugins/hypsometry'

        overrideLocale = QSettings().value('locale/overrideFlag', False,
                                           type=bool)
        if not overrideLocale:
            localeFullName = QLocale.system().name()
        else:
            localeFullName = QSettings().value('locale/userLocale', '')

        if QFileInfo(userPluginPath).exists():
            translationPath = userPluginPath + '/i18n/hypsometry_' \
                              + localeFullName + '.qm'
        else:
            translationPath = systemPluginPath + '/i18n/hypsometry_' \
                              + localeFullName + '.qm'

        self.localePath = translationPath
        if QFileInfo(self.localePath).exists():
            self.translator = QTranslator()
            self.translator.load(self.localePath)
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        if int(self.qgsVersion) < 20000:
            qgisVersion = self.qgsVersion[0] + '.' + self.qgsVersion[2] \
                          + '.' + self.qgsVersion[3]
            QMessageBox.warning(self.iface.mainWindow(), 'Hypsometry',
                    QCoreApplication.translate('Hypsometry',
                            'QGIS %s detected.\n') % (qgisVersion) +
                    QCoreApplication.translate('Hypsometry',
                            'This version of Hypsometry requires at least '
                            'QGIS 2.0.\nPlugin will not be enabled.'))
            return None

        self.actionRun = QAction(QCoreApplication.translate(
                'Hypsometry', 'Hypsometry'), self.iface.mainWindow())
        self.actionRun.setIcon(QIcon(':/icons/hypsometry.png'))
        self.actionRun.setWhatsThis('Run Hypsometry plugin')

        self.actionAbout = QAction(QCoreApplication.translate(
                'Hypsometry', 'About Hypsometry...'), self.iface.mainWindow())
        self.actionAbout.setIcon(QIcon(':/icons/about.png'))
        self.actionAbout.setWhatsThis('About Hypsometry')

        self.iface.addPluginToRasterMenu(QCoreApplication.translate(
                'Hypsometry', 'Hypsometry'), self.actionRun)
        self.iface.addPluginToRasterMenu(QCoreApplication.translate(
                'Hypsometry', 'Hypsometry'), self.actionAbout)

        self.iface.addRasterToolBarIcon(self.actionRun)

        self.actionRun.triggered.connect(self.run)
        self.actionAbout.triggered.connect(self.about)

    def unload(self):
        self.iface.removeRasterToolBarIcon(self.actionRun)

        self.iface.removePluginRasterMenu(QCoreApplication.translate(
                'Hypsometry', 'Hypsometry'), self.actionRun)
        self.iface.removePluginRasterMenu(QCoreApplication.translate(
                'Hypsometry', 'Hypsometry'), self.actionAbout)

    def run(self):
        dlg = hypsometrydialog.HypsometryDialog(self.iface)
        dlg.show()
        dlg.exec_()

    def about(self):
        dlg = aboutdialog.AboutDialog()
        dlg.exec_()
