import numpy as np
from osgeo import gdal

from .helpers import coord

def get_dataset(
        layer='http://mobileapp.nesdr.gov.in/out2019.tif',
        projWin=None,
        coord_sys="EPSG:4326",
        resample=True,
        scaleParams=True
        ):
    if projWin is not None:
        projWin = coord(projWin, coord_sys)
    dataset = gdal.Open(
        #'/vsicurl/'+layer,
        './main/out2019.tif',
        gdal.GA_ReadOnly
        )
    if scaleParams:
        stats = [dataset.GetRasterBand(i+1).GetStatistics(True, True) for i in range(dataset.RasterCount)]
        vmin, vmax, _, _ = zip(*stats)
        scaleParams = list(zip(*[vmin, vmax]))
    else:
        scaleParams = None
    if projWin is None and resample:
        dataset = gdal.Warp(
            '', dataset, width=256, height=256, format='MEM'
        )
    elif projWin is None:
        dataset = dataset
    elif not resample:
        dataset = gdal.Warp(
            '', dataset, outputBounds=projWin, format='MEM'
        )
    else:
        dataset = gdal.Warp(
            '', dataset, width=256, height=256, outputBounds=projWin, format='MEM'
        )
    return gdal.Translate('',dataset,scaleParams=scaleParams, format='MEM')

class B():
    def __init__(self,dataset=None, band_no=0, band=None, min=0, max=2500):
        if dataset is None:
            self._band = band
        else:
            self._band = dataset.GetRasterBand(band_no).ReadAsArray()
    
    @property
    def band(self):
        return self._band
    
    def __repr__(self):
        return self._band
    
    def __getitem__(self, index):
        return self.band[index]
    
    #Statistical Ops
    def mean(self):
        return np.mean(self._band)
    
    def max(self):
        return np.max(self._band)
    
    def min(self):
        return np.min(self._band)
    
    def std(self):
        return np.std(self._band)
    
    #Arithmetic Operations
    def __add__(self,y):
        return B(band=self._band+y.band)
    
    def __sub__(self, y):
        return B(band=self._band-y.band)
    
    def __mul__(self, y):
        if isinstance(y,B):
            return B(band=np.multiply(self._band,y.band))
        else:
            return B(band=self._band * y)
    
    def __truediv__(self, y):
        if isinstance(y,B):
            return B(band=np.divide(self._band, y.band, out=np.zeros_like(self._band), where=y.band!=0, casting="unsafe"))
        else:
            return B(band=self._band/y)
    
    #Bitwise Operators
    def __and__(self, y):
        return B(band=np.bitwise_and(self._band,y))
    
    def __or__(self, y):
        return B(band=np.bitwise_or(self._band,y))
    
    def __xor__(self, y):
        return B(band=np.bitwise_xor(self._band,y))
    
    def __invert__(self, y):
        return B(band=np.invert(self._band,y))
    
    #Comparison Operators    
    def __gt__(self, y):
        return B(band=np.array(self._band>y))
    
    def __ge__(self, y):
        return B(band=np.array(self._band>=y))

    def __lt__(self, y):
        return B(band=np.array(self._band<y))
    
    def __le__(self, y):
        return B(band=np.array(self._band<=y))
    
    def __eq__(self, y):
        return B(band=np.array(self._band==y))
    
    def __ne__(self, y):
        return B(band=np.array(self._band!=y))
    
    #Convolution Operations    
    def conv2D(self, kernel, padding=0, strides=1):
        image = self.band
        kernel = np.flipud(np.fliplr(kernel))
        xKernShape = kernel.shape[0]
        yKernShape = kernel.shape[1]
        xImgShape = image.shape[0]
        yImgShape = image.shape[1]
        xOutput = int(((xImgShape - xKernShape + 2 * padding) / strides) + 1)
        yOutput = int(((yImgShape - yKernShape + 2 * padding) / strides) + 1)
        output = np.zeros((xOutput, yOutput))
        if padding != 0:
            imagePadded = np.zeros((image.shape[0] + padding*2, image.shape[1] + padding*2))
            imagePadded[int(padding):int(-1 * padding), int(padding):int(-1 * padding)] = image
        else:
            imagePadded = image
        for y in range(image.shape[1]):
            if y > image.shape[1] - yKernShape:
                break
            if y % strides == 0:
                for x in range(image.shape[0]):
                    if x > image.shape[0] - xKernShape:
                        break
                    try:
                        if x % strides == 0:
                            output[x, y] = (kernel * imagePadded[x: x + xKernShape, y: y + yKernShape]).sum()
                    except:
                        break
        return B(band=output)