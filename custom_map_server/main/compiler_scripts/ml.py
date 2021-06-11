import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import os
from ..models import Model_cache
from .helpers import prepare_data, dict_hash
import time
from .basics import B
from .storage_paths import *

class RasterPCA():
    def __init__(self,n_components,dataset=None,bands=None,selected_bands=None,**kwargs):
        self.n_components = n_components
        if dataset is not None:
            if selected_bands is None:
                selected_bands = list(range(dataset.RasterCount))
            self.X = []
            for band in selected_bands:
                self.X.append(np.ravel(dataset.GetRasterBand(band).ReadAsArray()))
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
        b = [B(bands=r) for r in res]

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

            self.load(path=f'{RANDOM_FOREST_CACHE}/{self.sess_key}/{hash_val}.joblib')
        
        else:
            try:
                Model_cache.objects.create(sessHash=modelHashId,blocked=True)
                t = time.time()
                # BLOCKED SECTION
                if not os.path.exists(f'{RANDOM_FOREST_CACHE}/{self.sess_key}'):
                    os.mkdir(f'{RANDOM_FOREST_CACHE}/{self.sess_key}')
                X, y = prepare_data(
                    layer=data['layer'],coord_format=data['coord_format'],data=data['data'],bands=data['bands']
                )
                t = time.time()
                self.rf.fit(X, y)
                self.dump(path=f'{RANDOM_FOREST_CACHE}/{self.sess_key}/{hash_val}.joblib')
                m = Model_cache.objects.get(sessHash=modelHashId)
                m.blocked = False
                m.save()
                # END OF BLOCKED SECTION
            except:
                i = 0
                m = True
                while m:
                    if i%10000==0:
                        i = 0
                        m = Model_cache.objects.filter(sessHash=modelHashId).values_list('blocked')[0][0]
                    i += 1

                self.load(path=f'{RANDOM_FOREST_CACHE}/{self.sess_key}/{hash_val}.joblib')
            
    
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
        #cmap = plt.matplotlib.colors.ListedColormap(index_colors, 'Classification', n)
        return B(band=self.class_prediction)