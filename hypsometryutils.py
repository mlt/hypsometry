# -*- coding: utf-8 -*-

"""
***************************************************************************
    hypsometryutils.py
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

import locale

from PyQt4.QtCore import *

from qgis.core import *


def getPolygonLayerNames():
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    layerNames = []
    for name, layer in layerMap.iteritems():
        if layer.type() == QgsMapLayer.VectorLayer \
                and layer.geometryType() == QGis.Polygon:
            layerNames.append(unicode(layer.name()))
    return sorted(layerNames, cmp=locale.strcoll)


def getRasterLayerNames():
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    layerNames = []
    for name, layer in layerMap.iteritems():
        if layer.type() == QgsMapLayer.RasterLayer \
                and layer.providerType() == 'gdal':
            layerNames.append(unicode(layer.name()))
    return sorted(layerNames, cmp=locale.strcoll)


def getVectorLayerByName(layerName):
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    for name, layer in layerMap.iteritems():
        if layer.type() == QgsMapLayer.VectorLayer \
                and layer.name() == layerName:
            if layer.isValid():
                return layer
            else:
                return None


def getRasterLayerByName(layerName):
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    for name, layer in layerMap.iteritems():
        if layer.type() == QgsMapLayer.RasterLayer \
                and layer.name() == layerName \
                and layer.providerType() == 'gdal':
            if layer.isValid():
                return layer
            else:
                return None


def mapToPixel(mX, mY, geoTransform):
    if geoTransform[2] + geoTransform[4] == 0:
        pX = (mX - geoTransform[0]) / geoTransform[1]
        pY = (mY - geoTransform[3]) / geoTransform[5]
    else:
        (pX, pY) = applyGeoTransform(mX, mY, invertGeoTransform(geoTransform))
    return (int(pX), int(pY))


def pixelToMap(pX, pY, geoTransform):
    (mX, mY) = applyGeoTransform(pX + 0.5, pY + 0.5, geoTransform)
    return (mX, mY)


def applyGeoTransform(inX, inY, geoTransform):
    outX = geoTransform[0] + inX * geoTransform[1] + inY * geoTransform[2]
    outY = geoTransform[3] + inX * geoTransform[4] + inY * geoTransform[5]
    return (outX, outY)


def invertGeoTransform(geoTransform):
    det = geoTransform[1] * geoTransform[5] - geoTransform[2] * geoTransform[4]

    if abs(det) < 0.000000000000001:
        return

    invDet = 1.0 / det

    outGeoTransform = [0, 0, 0, 0, 0, 0]
    outGeoTransform[1] = geoTransform[5] * invDet
    outGeoTransform[4] = -geoTransform[4] * invDet

    outGeoTransform[2] = -geoTransform[2] * invDet
    outGeoTransform[5] = geoTransform[1] * invDet

    outGeoTransform[0] = (geoTransform[2] * geoTransform[3] - geoTransform[0]
                          * geoTransform[5]) * invDet
    outGeoTransform[3] = (-geoTransform[1] * geoTransform[3] + geoTransform[0]
                          * geoTransform[4]) * invDet

    return outGeoTransform
