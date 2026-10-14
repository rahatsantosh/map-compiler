'''
[User Accessible]
Core functionality for compiler script, including loading a GDAL dataset and performing basic
mathematical operations on bands and more advanced statistical operations.

Functions:

    get_dataset(string, list, string, bool, bool) -> osgeo.gdal.Dataset

Classes:

    B
'''

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
    """
    Load Optimized Geotiff of the specified region as a GDAL dataset, with the required
    stretching and resampling.

        Parameters
        ----------
            layer [string] -- Link to Remote Optimized-Geotiff layer
            projWin [list] -- List containing the bounding box
                coordinates i.e. 4 values or single point coordinate i.e. 2 values
            coord_sys [string] -- Coordinate system in which projWin is mentioned
            resample [bool] -- if True dataset is resampled to 256X256
            scaleParams [bool] -- if True dataset is scaled to [0, 256] else original range

        Returns
        -------
            osgeo.gdal.Dataset
    """
    if projWin is not None:
        projWin = coord(projWin, coord_sys)
    dataset = gdal.Open(
        #'/vsicurl/'+layer,
        './main/2019_NOV_DEC_compressed_resample.tif',
        #'/media/kitoo/Pers/nesac/2019_NOV_DEC_compressed.tif',
        #'./main/out2019.tif', # Path to Local Optimized-Geotiff for testing purposes
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


class B:
    """
    A class to represent a single raster Band, and further enabling a
    multitude of operations among multiple bands

    ...

    Attributes
    ----------
    band : np.ndarray
        selected band of certain GDAL dataset.

    Methods
    -------
    __repr__():
        Returns band attribute
    __getitem__(index:tuple):
        Returns pixel value at certain indices
    -------------------------Statistical Operations-------------------------
    mean(**kwargs):
        Returns mean value of band. Similar to np.mean
    max(**kwargs):
        Returns max value of band. Similar to np.max
    min(**kwargs):
        Returns min value of band. Similar to np.min
    std(**kwargs):
        Returns standard deviation value of band. Similar to np.std
    -------------------------Arithmetic Operations-------------------------
    __add__(y:.B): Operator -> +
        Returns band addition of self and y
    __sub__(y:.B): Operator -> -
        Returns band subtraction of self and y
    __mul__(y:.B or float): Operator -> *
        Returns elementwise band multiplication of self and y. y can be of type .B or simple float
    __truediv__(y:.B or float): Operator -> /
        Returns elementwise band division of self and y. y can be of type .B or simple float. Similar to np.divide.
        Zero cases handled.
    -------------------------Bitwise Operations-------------------------
    __and__(y:.B): Operator -> &
        Returns bitwise and of self and y
    __or__(y:.B): Operator -> |
        Returns bitwise or of self and y
    __xor__(y:.B): Operator -> ^
        Returns bitwise xor of self and y
    __invert__(y:.B): Operator -> ~
        Returns inverted band of self
    -------------------------Comparison Operations-------------------------
    __gt__(y:.B): Operator -> >
        Returns elementwise band comparison of self > y
    __ge__(y:.B): Operator -> >=
        Returns elementwise band comparison of self >= y
    __lt__(y:.B): Operator -> <
        Returns elementwise band comparison of self < y
    __le__(y:.B): Operator -> <=
        Returns elementwise band comparison of self <= y
    __eq__(y:.B): Operator -> ==
        Returns elementwise band comparison of self == y
    __ne__(y:.B): Operator -> !=
        Returns elementwise band comparison of self != y
    -------------------------Convolution Operation-------------------------
    conv2D(kernel:np.array, padding:int, strides:int):
        Returns 2D convolution applied on band, using custom kernel
    """
    def __init__(self,dataset=None, band_no=0, band=None):
        """
        Constructor

        Parameters
        ----------
            dataset : osgeo.gdal.Dataset
                GDAL Dataset object from which raster band is to be extracted
            band_no : int
                Band number to be extracted
            band : np.array
                Alternatively, required band is directly given as an numpy 2D array. In this case
                dataset and band_no parameters are to be left to default
        """
        if dataset is None:
            self._band = band
        else:
            self._band = dataset.GetRasterBand(band_no).ReadAsArray()

    @property
    def band(self):
        """
        [Property]
        Returns self._band attribute
        """
        return self._band

    def __repr__(self):
        """
        Invoked when attempting to display object.
        Returns band attribute
        """
        return self._band

    def __getitem__(self, index):
        """
        Invoked when object called as iterable.
        Returns pixel value
        """
        return self.band[index]

    #Statistical Operations
    def mean(self, **kwargs):
        """
        Wrapper for np.mean, finds mean value of band.
        Parameters same as np.mean
        Returns mean value
        """
        return np.mean(self._band, **kwargs)

    def max(self, **kwargs):
        """
        Wrapper for np.ax, finds max value of band.
        Parameters same as np.max
        Returns max value
        """
        return np.max(self._band, **kwargs)

    def min(self, **kwargs):
        """
        Wrapper for np.min, finds min value of band.
        Parameters same as np.min
        Returns min value
        """
        return np.min(self._band, **kwargs)

    def std(self, **kwargs):
        """
        Wrapper for np.std, finds std value of band.
        Parameters same as np.std
        Returns std value
        """
        return np.std(self._band, **kwargs)

    #Arithmetic Operations
    def __add__(self,y):
        """
        [Operator Overloading]
        Simple addition between self and y

        Parameters
        ----------
            y : .B
                Band to be added to self

        Returns: .B
            self._band + y._band
        """
        return B(band=self._band+y.band)

    def __sub__(self, y):
        """
        [Operator Overloading]
        Simple subtraction between self and y

        Parameters
        ----------
            y : .B
                Band to be subtracted from self

        Returns: .B
            self._band - y._band
        """
        return B(band=self._band-y.band)

    def __mul__(self, y):
        """
        [Operator Overloading]
        Simple multiplication between self and y

        Parameters
        ----------
            y : .B (or) float
                Band to be multiplied to self, (or) decimal number to be multiplied

        Returns: .B
            self._band * y._band (or) self._band * y
        """
        if isinstance(y,B):
            return B(band=np.multiply(self._band,y.band))
        else:
            return B(band=self._band * y)

    def __truediv__(self, y):
        """
        [Operator Overloading]
        Simple division between self and y. Zero cases handled using out and where parameter of np.divide
        Wrapper for np.divide

        Parameters
        ----------
            y : .B (or) float
                Band to be divided with self, (or) decimal number to be divided

        Returns: .B
            self._band / y._band (or) self._band / y
        """
        if isinstance(y,B):
            return B(band=np.divide(self._band, y.band, out=np.zeros_like(self._band), where=y.band!=0, casting="unsafe"))
        else:
            return B(band=self._band/y)

    #Bitwise Operators
    def __and__(self, y):
        """
        [Operator Overloading]
        Simple bitwise and between self and y.
        Wrapper for np.bitwise_and

        Parameters
        ----------
            y : .B
                Band to perform bitwise and with self

        Returns: .B
            self._band & y._band
        """
        return B(band=np.bitwise_and(self._band,y))

    def __or__(self, y):
        """
        [Operator Overloading]
        Simple bitwise or between self and y.
        Wrapper for np.bitwise_or

        Parameters
        ----------
            y : .B
                Band to perform bitwise or with self

        Returns: .B
            self._band | y._band
        """
        return B(band=np.bitwise_or(self._band,y))

    def __xor__(self, y):
        """
        [Operator Overloading]
        Simple bitwise xor between self and y.
        Wrapper for np.bitwise_xor

        Parameters
        ----------
            y : .B
                Band to perform bitwise xor with self

        Returns: .B
            self._band ^ y._band
        """
        return B(band=np.bitwise_xor(self._band,y))

    def __invert__(self):
        """
        [Operator Overloading]
        Simple bitwise not operator on y.
        Wrapper for np.invert

        Returns: .B
            ~self._band
        """
        return B(band=np.invert(self._band))

    #Comparison Operators
    def __gt__(self, y):
        """
        [Operator Overloading]
        Simple greater than comparison between self and y.
        Elementwise, returns 1 of self > y else returns 0.

        Parameters
        ----------
            y : .B
                Band object to compare with self

        Returns: .B
            self._band > y._band
        """
        return B(band=np.array(self._band>y))

    def __ge__(self, y):
        """
        [Operator Overloading]
        Simple greater than or equal comparison between self and y.
        Elementwise, returns 1 of self >= y else returns 0.

        Parameters
        ----------
            y : .B
                Band object to compare with self

        Returns: .B
            self._band >= y._band
        """
        return B(band=np.array(self._band>=y))

    def __lt__(self, y):
        """
        [Operator Overloading]
        Simple less than comparison between self and y.
        Elementwise, returns 1 of self < y else returns 0.

        Parameters
        ----------
            y : .B
                Band object to compare with self

        Returns: .B
            self._band < y._band
        """
        return B(band=np.array(self._band<y))

    def __le__(self, y):
        """
        [Operator Overloading]
        Simple less than or equal comparison between self and y.
        Elementwise, returns 1 of self <= y else returns 0.

        Parameters
        ----------
            y : .B
                Band object to compare with self

        Returns: .B
            self._band <= y._band
        """
        return B(band=np.array(self._band<=y))

    def __eq__(self, y):
        """
        [Operator Overloading]
        Simple equal to comparison between self and y.
        Elementwise, returns 1 of self == y else returns 0.

        Parameters
        ----------
            y : .B
                Band object to compare with self

        Returns: .B
            self._band == y._band
        """
        return B(band=np.array(self._band==y))

    def __ne__(self, y):
        """
        [Operator Overloading]
        Simple not equal comparison between self and y.
        Elementwise, returns 1 of self != y else returns 0.

        Parameters
        ----------
            y : .B
                Band object to compare with self

        Returns: .B
            self._band != y._band
        """
        return B(band=np.array(self._band!=y))

    #Convolution Operation
    def conv2D(self, kernel, padding=0, strides=1):
        """
        2D convolution operation on band.

        Parameters
        ----------
            kernel : list
                Custom covolution kernel. List of len 2
            padding : int
                Input band padding size
            strides : int
                Convolution stride size

        Returns:
            .B object containing Convolution result
        """
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
                    except Exception:
                        break
        return B(band=output)
