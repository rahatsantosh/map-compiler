import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import PCA
import os
from ..models import Model_cache
from .helpers import prepare_data, dict_hash
import time
from .basics import B, get_dataset
from .storage_paths import *


class RasterPCA():
    def __init__(self,sess_key,saved_path=None,**kwargs):
        self.pca = joblib.load(saved_path) if saved_path is not None else PCA(**kwargs)
        self.sess_key = sess_key
    
    def dump(self, path):
        joblib.dump(self.pca, path)
    
    def load(self, path):
        self.pca = joblib.load(path)
    
    def __prepare_train_data(self,data):
        d = get_dataset(layer = data['layer'])
        return np.array(
            [d.GetRasterBand(i).ReadAsArray().ravel() for i in data['bands']]
        ).T
    
    def __prepare_infer_data(self,dataset=None,n_bands=None,bands=None):
        if dataset is None and bands is not None:
            X = np.asarray([band.band.ravel() for band in bands]).T
        elif bands is None and dataset is not None:
            X = np.array([dataset.GetRasterBand(i).ReadAsArray().ravel() for i in n_bands]).T
        else:
            exit(0)
        return X
    
    def fit(self, data):
        '''
        data: dict
        {
        'layer':layer,
        'bands':bands_list
        }
        '''
        hash_val = dict_hash(data)
        modelHashId = self.sess_key + str(hash_val)

        if Model_cache.objects.filter(sessHash=modelHashId).exists():
            i = 0
            m = True
            while m:
                if i%10000==0:
                    i = 0
                    m = Model_cache.objects.filter(sessHash=modelHashId).values_list('blocked')[0][0]
                i += 1
            self.load(path=f'{PCA_CACHE}/{self.sess_key}/{hash_val}.joblib')
        else:
            try:
                Model_cache.objects.create(sessHash=modelHashId,blocked=True)
                # BLOCKED SECTION
                if not os.path.exists(f'{PCA_CACHE}/{self.sess_key}'):
                    os.mkdir(f'{PCA_CACHE}/{self.sess_key}')
                X = self.__prepare_train_data(data)
                self.pca.fit(X)
                self.dump(path=f'{PCA_CACHE}/{self.sess_key}/{hash_val}.joblib')
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
                self.load(path=f'{PCA_CACHE}/{self.sess_key}/{hash_val}.joblib')
    
    def transform(self,**kwargs):
        X = self.__prepare_infer_data(**kwargs)
        X = self.pca.transform(X)
        X = X.reshape((256,256,self.pca.n_components))
        return B(band=X)


class RandomForest(object):
    def __init__(self,sess_key,saved_path=None,**kwargs):
        self.rf = joblib.load(saved_path) if saved_path is not None else RandomForestClassifier(**kwargs)
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
        return B(band=self.class_prediction)

