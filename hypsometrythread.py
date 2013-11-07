# -*- coding: utf-8 -*-

"""
***************************************************************************
    hypsometrythread.py
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

import os

import numpy
from osgeo import gdal, ogr, osr
from PyQt4.QtCore import *
from qgis.core import *

import unicodewriter
import hypsometryutils as utils


class HypsometryThread(QThread):
    rangeChanged = pyqtSignal(int)
    updateProgress = pyqtSignal()
    processFinished = pyqtSignal()
    processInterrupted = pyqtSignal()

    def __init__(self, raster, vector, step, directory, percentage):
        QThread.__init__(self, QThread.currentThread())
        self.mutex = QMutex()
        self.stopMe = 0
        self.interrupted = False

        self.rasterPath = raster
        self.vector = vector
        self.step = step
        self.outputDirectory = directory
        self.percentage = percentage

    def run(self):
        rasterDS = gdal.Open(self.rasterPath, gdal.GA_ReadOnly)
        geoTransform = rasterDS.GetGeoTransform()
        rasterBand = rasterDS.GetRasterBand(1)
        noData = rasterBand.GetNoDataValue()

        cellXSize = abs(geoTransform[1])
        cellYSize = abs(geoTransform[5])
        rasterXSize = rasterDS.RasterXSize
        rasterYSize = rasterDS.RasterYSize

        rasterBBox = QgsRectangle(geoTransform[0], geoTransform[3] - cellYSize
                                  * rasterYSize, geoTransform[0] + cellXSize
                                  * rasterXSize, geoTransform[3])

        rasterGeom = QgsGeometry.fromRect(rasterBBox)

        crs = osr.SpatialReference()
        crs.ImportFromProj4(str(self.vector.crs().toProj4()))

        memVectorDriver = ogr.GetDriverByName('Memory')
        memRasterDriver = gdal.GetDriverByName('MEM')

        self.rangeChanged.emit(self.vector.featureCount())
        for f in self.vector.getFeatures():
            geom = f.geometry()

            intersectedGeom = rasterGeom.intersection(geom)
            ogrGeom = ogr.CreateGeometryFromWkt(intersectedGeom.exportToWkt())

            bbox = intersectedGeom.boundingBox()
            xMin = bbox.xMinimum()
            xMax = bbox.xMaximum()
            yMin = bbox.yMinimum()
            yMax = bbox.yMaximum()

            (startColumn, startRow) = utils.mapToPixel(xMin, yMax,
                                                       geoTransform)
            (endColumn, endRow) = utils.mapToPixel(xMax, yMin, geoTransform)

            width = endColumn - startColumn
            height = endRow - startRow

            if width == 0 or height == 0:
                self.updateProgress.emit()

                self.mutex.lock()
                s = self.stopMe
                self.mutex.unlock()
                if s == 1:
                    self.interrupted = True
                    break

                continue

            srcOffset = (startColumn, startRow, width, height)
            srcArray = rasterBand.ReadAsArray(*srcOffset)

            newGeoTransform = (
                geoTransform[0] + srcOffset[0] * geoTransform[1],
                geoTransform[1],
                0.0,
                geoTransform[3] + srcOffset[1] * geoTransform[5],
                0.0,
                geoTransform[5]
                )

            memVDS = memVectorDriver.CreateDataSource('out')
            memLayer = memVDS.CreateLayer('poly', crs, ogr.wkbPolygon)

            ft = ogr.Feature(memLayer.GetLayerDefn())
            ft.SetGeometry(ogrGeom)
            memLayer.CreateFeature(ft)
            ft.Destroy()

            rasterizedDS = memRasterDriver.Create('', srcOffset[2],
                    srcOffset[3], 1, gdal.GDT_Byte)
            rasterizedDS.SetGeoTransform(newGeoTransform)
            gdal.RasterizeLayer(rasterizedDS, [1], memLayer, burn_values=[1])
            rasterizedArray = rasterizedDS.ReadAsArray()

            srcArray = numpy.nan_to_num(srcArray)
            masked = numpy.ma.MaskedArray(srcArray,
                    mask=numpy.logical_or(srcArray == noData,
                    numpy.logical_not(rasterizedArray)))

            # TODO: calculate curve
            self.calculateHypsometry(f.id(), masked, cellXSize, cellYSize)

            memVDS = None
            rasterizedDS = None

            self.updateProgress.emit()

            self.mutex.lock()
            s = self.stopMe
            self.mutex.unlock()
            if s == 1:
                self.interrupted = True
                break

        rasterDS = None

        if not self.interrupted:
            self.processFinished.emit()
        else:
            self.processInterrupted.emit()

    def stop(self):
        self.mutex.lock()
        self.stopMe = 1
        self.mutex.unlock()

        QThread.wait(self)

    def calculateHypsometry(self, fid, data, pX, pY):
        out = dict()
        d = data.compressed()
        if d.size == 0:
            return
        minValue = d.min()
        maxValue = d.max()
        startValue = minValue
        tmpValue = minValue + self.step
        while startValue < maxValue:
            out[tmpValue] = ((startValue <= d) & (d < tmpValue)).sum()
            startValue = tmpValue
            tmpValue += self.step

        if self.percentage:
            multiplier = 100.0 / float(len(d.flat))
        else:
            multiplier = pX * pY
        for k, v in out.iteritems():
            out[k] = v * multiplier

        prev = None
        for i in sorted(out.items()):
            if prev is None:
                out[i[0]] = i[1]
            else:
                out[i[0]] = i[1] + out[prev]
            prev = i[0]

        fName = os.path.join(self.outputDirectory,
                             'hystogram_%s_%s.csv' % (self.vector.name(), fid))

        csvFile = open(fName, 'wb')
        writer = unicodewriter.UnicodeWriter(csvFile)
        writer.writerow(['Area', 'Elevation'])
        for i in sorted(out.items()):
            writer.writerow([i[1], i[0]])
        csvFile.close()
        del writer
