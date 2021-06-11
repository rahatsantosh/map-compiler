from osgeo import gdal, osr
import numpy as np
import time
from PIL import Image
import cv2
import matplotlib.pyplot as plt
from django.http import HttpResponse
from .helpers import coord, norm, apply_cmap, prepare_data, dict_hash
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import os
from ..models import Model_cache

'''
django sessions
Sample script:

d = get_dataset(resample=False)
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
ndvi = (b-g)/(b+g)
#response = setup(ndvi)
#print(ndvi.band)
graph = rasterPlot(d,[94.589,27.523],'EPSG:4326')

d = get_dataset()
r = B(dataset=d, band_no=3)
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
response = setup(
  r,g,b,
  ip_minR=0,ip_maxR=12252,
  ip_minB=0,ip_maxB=12211,
  ip_minG=0,ip_maxG=12536,
)

d = get_dataset()
r1 = B(dataset=d, band_no=3)
r2 = B(dataset=d, band_no=1)
r = r1 + r2
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
response = setup(
  r,g,b,
  ip_minR=0,ip_maxR=1000,
  ip_minB=0,ip_maxB=2000,
  ip_minG=0,ip_maxG=2000,
)

d = get_dataset()
r1 = B(dataset=d, band_no=3)
r2 = B(dataset=d, band_no=1)
r = r1 + r2
response = setup(
  r,
  ip_minR=0, ip_maxR=2000
)

d = get_dataset()
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
ndvi = (b-g)/(b+g)
response = setup(
  ndvi,
  op_minR=0.5,
)

d = get_dataset()
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
ndvi = (b-g)/(b+g)
response = setup(ndvi)

d = get_dataset()
rf = RandomForest(saved_path='./main/model1.joblib')
colors = dict((
    (0, (0, 0, 0)),  # Nodata
    (1, (0, 150, 0)),  # Forest
    (2, (0, 0, 255)),  # Water
    (3, (0, 255, 0)),  # Herbaceous
    (4, (160, 82, 45)),  # Barren
    (5, (255, 0, 0))  # Urban
))
rf.colormap = colors
response = setup(
    R=rf.predict(d,[1,2,3,4,5,6,7]).prediction_map,
    ip_minR=1, ip_maxR=7,
    cmap=colors
)

d = get_dataset()
rf = RandomForest(max_depth=2, n_estimators=500)
colors = dict((
    (0, (0, 0, 0)),  # Nodata
    (1, (0, 150, 0)),  # Forest
    (2, (0, 0, 255)),  # Water
    (3, (0, 255, 0)),  # Herbaceous
    (4, (160, 82, 45)),  # Barren
    (5, (255, 0, 0))  # Urban
))
rf.colormap = colors
data = {
		'layer':'aa',
  	'coord_format':'EPSG:4326',
  	'bands':[2,3,4,5],
  	'data':[
      	{'coordinates':[94.939,27.357],'labels':1},
        {'coordinates':[95.051,27.911],'labels':2},
        {'coordinates':[94.627,27.839],'labels':1},
        {'coordinates':[94.844,27.921],'labels':3},
        {'coordinates':[95.028,27.790],'labels':2},
        {'coordinates':[95.104,27.672],'labels':2},
        {'coordinates':[95.014,27.576],'labels':3},
        {'coordinates':[94.210,27.203],'labels':1},
        {'coordinates':[94.369,27.552],'labels':1},
        {'coordinates':[94.036,27.993],'labels':3},
        {'coordinates':[94.718,27.879],'labels':3},
        {'coordinates':[94.780,27.627],'labels':1},
        {'coordinates':[94.490,27.555],'labels':2},
        {'coordinates':[94.752,27.526],'labels':1},
        {'coordinates':[95.089,27.065],'labels':2}]
}
rf.fit(data)
response = setup(
    R=rf.predict(d,[2,3,4,5]).prediction_map,
    ip_minR=1, ip_maxR=7,
    cmap=colors
)

d = get_dataset()
g = B(dataset=d, band_no=4)
b = B(dataset=d, band_no=8)
ndvi = (b-g)/(b+g)
response = setup(
				R=ndvi.conv2D(kernel=[[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
        )

Sample url request:
http://127.0.0.1:8000/wms/?service=WMS&
request=GetMap&
layers=&styles=&format=image%2Fjpeg&
transparent=false&
version=1.1.1&
request_script=d%20%3D%20get_dataset()%0Ar1%20%3D%20B(d%2C%203)%0Ar2%20%3D%20B(d%2C%201)%0Ar%20%3D%20r1%20%2B%20r2%0Ag%20%3D%20B(d%2C%204)%0Ab%20%3D%20B(d%2C%208)%0Asetup(r%2Cg%2Cb)&
width=256&
height=256&
srs=EPSG%3A3857&
bbox=10488383.273178745,3248267.954006849,10527519.031660756,3287403.7124888618
'''


def get_dataset(layer='http://mobileapp.nesdr.gov.in/out2019.tif', projWin=None, coord_sys="EPSG:4326",resample=True):
    if projWin is not None:
        projWin = coord(projWin, coord_sys)
    dataset = gdal.Open(
        #'/vsicurl/'+layer,
        './main/out2019.tif',
        gdal.GA_ReadOnly
        )
    if projWin is None and resample:
        return gdal.Warp(
            '', dataset, width=256, height=256, format='MEM'
        )
    elif projWin is None:
        return dataset
    else:
        return gdal.Warp(
            '', dataset, width=256, height=256, outputBounds=projWin, format='MEM'
        )

class B():
    def __init__(self,dataset=None, band_no=0, band=None, min=0, max=2500):
        if dataset is None:
            self._band = band
        else:
            self._band = norm(x=np.array(dataset.GetRasterBand(band_no).ReadAsArray()),ip_minR=min,ip_maxR=max)
    
    @property
    def band(self):
        return self._band
    
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

def rasterPlot(dataset, coordinate, coord_format, bands=None, style='bar'):
    if bands is None:
        bands = list(range(1,dataset.RasterCount+1))
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize
    proj = osr.SpatialReference(wkt=dataset.GetProjection())
    epsg = "EPSG:"+str(proj.GetAttrValue('AUTHORITY',1))
    coordinates = coord(coordinate, coord_sys=epsg, src_coord_sys=coord_format)

    transform = dataset.GetGeoTransform()

    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = -transform[5]
    col = int((coordinates[0] - xOrigin) / pixelWidth)
    row = int((yOrigin - coordinates[1] ) / pixelHeight)

    def prepare_data_bandwise(band):
        band = dataset.GetRasterBand(band)
        data = band.ReadAsArray(0, 0, cols, rows).tolist()
        return data[row][col]

    band_data = list(map(prepare_data_bandwise,bands))
    labels = bands
    graph = {
        'type':style,
        'data':{
            'labels':labels,
            'datasets':[{
                'data':band_data
            }]
        }
    }

    return graph
    
class RasterPCA():
    def __init__(self,n_components,dataset=None,bands=None,selected_bands=None,**kwargs):
        self.n_components = n_components
        if dataset is not None:
            if selected_bands is None:
                selected_bands = list(range(dataset.RasterCount))
            self.X = []
            for band in selected_bands:
                self.X.append(np.ravel(dataset.GetRasterBand(band).ReadAsArray()))
            self.X = np.asarray(self.X)
        else:
            self.X = []
            for band in bands:
                self.X.append(band.band)
            self.X = np.asarray(self.X)
        self.shape = self.X.shape
        self.sc = StandardScaler()
        self.X = self.sc.fit_transform(self.X)
        self.X = np.reshape(self.X,(-1,self.X.shape[2]))
        self.pca = PCA(self.n_components,**kwargs)
    
    @property
    def fit(self):
        self.pca.fit(self.X)
    
    @property
    def transform(self):
        res = np.reshape(self.pca.transform(self.X),(self.shape[0],self.shape[1],self.n_components))
        if self.n_components == 1:
            return B(bands=res)
        b = []
        for r in res:
            b.append(B(bands=r))

    @property
    def fit_transform(self):
        return np.reshape(self.pca.fit_transform(self.X),(self.shape[0],self.shape[1],self.n_components))




# class RasterPCA(TransformerMixin):
#     def __init__(self, n_components, saved_path=None, **kwargs):
#         if saved_path is not None:
#             self.pca = joblib.load(saved_path)
#         else:
#             self.pca = PCA(n_components=n_components, **kwargs)
#         self.shape = None
#         self.n_bands = 0
    
#     def dump(self, path):
#         joblib.dump(self.pca, path)
    
#     def load(self, path):
#         self.pca = joblib.load(path)
    
#     def fit(self, dataset, bands):
#         self.n_bands = len(bands)
#         self.shape = (dataset.RasterXSize, dataset.RasterYSize)
#         X = []
#         for band in bands:
#             X.append(np.ravel(dataset.GetRasterBand(band).ReadAsArray()))
#         self.pca.fit(X)
    
#     def transform(self, dataset, bands):
#         assert len(bands) == self.n_bands
#         X = []
#         for band in bands:
#             X.append(dataset.GetRasterBand(band).ReadAsArray())
#         X = np.ravel(np.asarray(X))
#         X = self.pca.transform(X)
#         X = X.reshape((self.shape[0],self.shape[1],-1))
#         return X
    
#     def fit_transform(self, dataset, bands):
#         self.n_bands = len(bands)
#         self.shape = (dataset.RasterXSize, dataset.RasterYSize)
#         print(self.shape,'=============================')
#         X = []
#         for band in bands:
#             X.append(np.ravel(dataset.GetRasterBand(band).ReadAsArray()))
#         X = self.pca.fit_transform(X)
#         X = X.reshape((self.shape[0],self.shape[1],-1))
#         return X

class RandomForest(object):
    def __init__(self,sess_key,saved_path=None,**kwargs):
        if saved_path is not None:
            self.rf = joblib.load(saved_path)
        else:
            self.rf = RandomForestClassifier(**kwargs)
        self.colors = ()
        self.class_prediction = None
        self.sess_key = sess_key
    
    def dump(self, path):
        joblib.dump(self.rf, path)
    
    def load(self, path):
        self.rf = joblib.load(path)
    
    def fit(self, data):
        '''
        Format 
        {
            'layer':layer,
            'coord_format':coord_format,
            'bands':bands_list
            'data':[
                {'coordinates':X,'labels':y},
                ...
            ]
        }
        '''
        '''data = {
		'layer':'aa',
        'coord_format':'EPSG:4326',
        'bands':[2,3,4,5],
        'data':[
            {'coordinates':[94.939,27.357],'labels':1},
            {'coordinates':[95.051,27.911],'labels':2},
            {'coordinates':[94.627,27.839],'labels':1},
            {'coordinates':[94.844,27.921],'labels':3},
            {'coordinates':[95.028,27.790],'labels':2},
            {'coordinates':[95.104,27.672],'labels':2},
            {'coordinates':[95.014,27.576],'labels':3},
            {'coordinates':[94.210,27.203],'labels':1},
            {'coordinates':[94.369,27.552],'labels':1},
            {'coordinates':[94.036,27.993],'labels':3},
            {'coordinates':[94.718,27.879],'labels':3},
            {'coordinates':[94.780,27.627],'labels':1},
            {'coordinates':[94.490,27.555],'labels':2},
            {'coordinates':[94.752,27.526],'labels':1},
            {'coordinates':[95.089,27.065],'labels':2}]
        }'''
        hash_val = dict_hash(data)
        modelHashId = self.sess_key + str(hash_val)

        if Model_cache.objects.filter(sessHash=modelHashId).exists():
            time.sleep(15)
            i = 0
            m = True
            while m:
                if i%10000==0:
                    i = 0
                    m = Model_cache.objects.filter(sessHash=modelHashId).values_list('blocked')[0][0]
                i += 1

            self.load(path=f'./cache/random_forest/{self.sess_key}/{hash_val}.joblib')
        
        else:
            try:
                Model_cache.objects.create(sessHash=modelHashId,blocked=True)
                t = time.time()
                # BLOCKED SECTION
                if not os.path.exists(f'./cache/random_forest/{self.sess_key}'):
                    os.mkdir(f'./cache/random_forest/{self.sess_key}')
                X, y = prepare_data(
                    layer=data['layer'],coord_format=data['coord_format'],data=data['data'],bands=data['bands']
                )
                t = time.time()
                self.rf.fit(X, y)
                self.dump(path=f'./cache/random_forest/{self.sess_key}/{hash_val}.joblib')
                m = Model_cache.objects.get(sessHash=modelHashId)
                m.blocked = False
                m.save()
                #print('============',Model_cache.objects.filter(sessHash=modelHashId).values_list('blocked')[0][0])
                # END OF BLOCKED SECTION
            except:
                i = 0
                m = True
                while m:
                    if i%10000==0:
                        i = 0
                        m = Model_cache.objects.filter(sessHash=modelHashId).values_list('blocked')[0][0]
                    i += 1

                self.load(path=f'./cache/random_forest/{self.sess_key}/{hash_val}.joblib')
            
    
    def colormap(self, colors):
        self.colors = colors
    
    def predict(self, img, bands, index=[4,3,2], minmax=(0,8000)):
        img = img.ReadAsArray()
        img = np.moveaxis(img, 0, -1)
        img_as_array = np.take(img, bands, 2).reshape(-1,len(bands))
        self.class_prediction = self.rf.predict(img_as_array)
        self.class_prediction = self.class_prediction.reshape(img[:, :, 0].shape)
        
        return self
    
    @property
    def prediction_map(self):
        n = self.class_prediction.max()
        for k in self.colors:
            v = self.colors[k]
            _v = [_v / 255.0 for _v in v]
            self.colors[k] = _v
        index_colors = [self.colors[key] if key in self.colors else (255, 255, 255, 0) for key in range(1, n + 1)]
        cmap = plt.matplotlib.colors.ListedColormap(index_colors, 'Classification', n)
        return B(band=self.class_prediction)

def setup(
    R, G=None, B=None,
    weight=None, 
    op_minR=0, op_maxR=1, 
    op_minG=0, op_maxG=1, 
    op_minB=0, op_maxB=1,  
    ip_minR=-0.5, ip_maxR=0.8, 
    ip_minG=-0.5, ip_maxG=0.8, 
    ip_minB=-0.5, ip_maxB=0.8,
    cmap=None,
    cmap_order=1
    ):
    if (np.max(R.band)==0 and G is None and B is None) or (np.max(R.band)==0 and np.max(G.band)==0 and np.max(B.band)==0):
        im = np.zeros((256,256,4))
        img = Image.fromarray(im, mode='RGBA')
        response = HttpResponse(content_type="image/png")
        img.save(response, "PNG")
        return response
    if weight is None:
        weight = [1,1,1]
    if G is None and B is None:
        im  = weight[0] * R.band
        if cmap is not None and cmap_order==1:
            im = apply_cmap(im, cmap)
        im = np.array(norm(
            x = im,
            op_minR=op_minR, op_maxR=op_maxR,
            ip_minR=ip_minR, ip_maxR=ip_maxR))
        if cmap is not None and cmap_order==0:
            im = apply_cmap(im, cmap)
    else:
        x,y,z = norm(
            x=weight[0]*R.band, 
            y=weight[1]*G.band, 
            z=weight[2]*B.band,
            op_minR=op_minR, op_maxR=op_maxR,
            op_minG=op_minG, op_maxG=op_maxG,
            op_minB=op_minB, op_maxB=op_maxB,
            ip_minR=ip_minR, ip_maxR=ip_maxR,
            ip_minG=ip_minG, ip_maxG=ip_maxG,
            ip_minB=ip_minB, ip_maxB=ip_maxB)
        im = np.dstack((R.band,G.band,B.band)) 
    _, ar = cv2.imencode('.png',im)
    response = HttpResponse(ar.tobytes(),content_type="image/png")
    return response

'''def setup(R, G=None, B=None, weight=None, minR=0, maxR=1, minG=0, maxG=1, minB=0, maxB=1):
    if weight is None:
        weight = [1,1,1]
    elif len(weight) < 3:
        weight = [weights[0]] * 3
    if G is None and B is None:
        grayscale = True
        R = norm(R.band, G, B, minR, maxR, minG, maxG, minB, maxB) * weight[0]
    else:
        grayscale = False
        R = R.band
        G = G.band
        B = B.band
        R, G, B = norm(R, G, B, minR, maxR, minG, maxG, minB, maxB)
        R, G, B = R * weight[0], G * weight[1], B * weight[2]
    if G is None and B is None:
        grayscale = True
    else:
        grayscale = False
    return to_map(R=R, G=G, B=B, grayscale=grayscale)'''
