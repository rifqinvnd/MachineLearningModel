# -*- coding: utf-8 -*-
"""Rifqi Novandi_TimeSeries_Submission.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Zw0dxKS__Xvxwp5jongjt1og2F4mGSLJ
"""

# Dataset Source (https://data.world/data-society/global-climate-change-data/workspace/file?filename=GlobalLandTemperatures%2FGlobalLandTemperaturesByCountry.csv)

import pandas as pd
globaltempdf = pd.read_csv('GlobalLandTemperatures_GlobalLandTemperaturesByMajorCity.csv')
globaltempdf

# Hilangkan kolom yang tidak terpakai

globaltempdf = globaltempdf.drop(columns=['AverageTemperatureUncertainty', 'City', 'Latitude', 'Longitude'])
globaltempdf

# Ubah kolom dt menjadi datetime

globaltempdf['dt'] = pd.to_datetime(globaltempdf['dt'])
globaltempdf = globaltempdf.rename(columns={'dt': 'Date'})
globaltempdf

# buat dataframe baru yang berisikan country china

chinatempdf = globaltempdf.loc[globaltempdf['Country'].isin(['China'])]
chinatempdf

# menghilangkan kolom country karena sudah tidak terpakai

chinatempdf = chinatempdf.drop(columns=['Country']).reset_index(drop=True)
chinatempdf

# drop tabel yang kosong dan cek menggunakan fungsi isnull()

chinatempdf = chinatempdf.dropna(subset=['AverageTemperature'])
chinatempdf.isnull().sum()

# membatasi dataset menjadi 100 tahun

date_range = (chinatempdf['Date'] > '1913-01-01') & (chinatempdf['Date'] <= '2013-08-01')
chinatempdf = chinatempdf.loc[date_range]
chinatempdf

# plot grafik

import matplotlib.pyplot as plt

date = chinatempdf['Date'].values
avg_temp  = chinatempdf['AverageTemperature'].values

plt.figure(figsize=(15,10))
plt.plot(date, avg_temp)
plt.title(
    'Average Temperature in China for 100 Years from 1913 - 2013',
    fontsize=20
)
plt.show()

# menggunakan fungsi yang dapat diproses oleh model

import tensorflow as tf
from tensorflow.keras import layers

def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.map(lambda w: (w[:-1], w[-1:]))
    return ds.batch(batch_size).prefetch(1)

# train test split dengan validation 20 %

from sklearn.model_selection import train_test_split

X_train, X_test, Y_train, Y_test = train_test_split(avg_temp, date, test_size = 0.2, shuffle=False)

print(X_train.shape, Y_train.shape)
print(X_test.shape, Y_test.shape)

# masukan train test kepada fungsi sebelumnya

train_set = windowed_dataset(X_train, window_size=32, batch_size=64, shuffle_buffer=2500)
test_set = windowed_dataset(X_test, window_size=32, batch_size=64, shuffle_buffer=2500)

# menggunakan sequential dengan 2 layer LSTM da 2 Dense

from tensorflow.keras.models import Sequential
from tensorflow import keras
from tensorflow.keras import layers

model = Sequential([
                    layers.LSTM(64, return_sequences=True),
                    layers.LSTM(64),
                    layers.Dense(256, activation="relu"),
                    layers.Dense(1)
])

# Hitung MAE

MAE = 0.1*(chinatempdf['AverageTemperature'].max() - chinatempdf['AverageTemperature'].min())
print(MAE)

# Buat Callback untuk menghentikan training saat MAE < 10 %

class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('mae') < MAE and logs.get('val_mae') < MAE):
      print('\nSelamat MAE dari model < 10% skala data')
      self.model.stop_training = True
callbacks = myCallback()

# compile model dengan opttiizer

optimizer = tf.keras.optimizers.SGD(
    learning_rate=1e-3,
    momentum=0.2
)
model.compile(
    loss=tf.keras.losses.Huber(),
    optimizer=optimizer,
    metrics=['mae']
)

# train model

hist = model.fit(
    train_set,
    epochs=100,
    validation_data=test_set,
    callbacks=[callbacks]
)

# grafik plot MAE

plt.plot(hist.history['mae'])
plt.plot(hist.history['val_mae'])
plt.title('Grafik Plot MAE Model')
plt.ylabel('MAE')
plt.xlabel('Epoch')
plt.legend(['Train', 'Test'], loc='upper right')
plt.show()

# grafik plot loss

plt.plot(hist.history['loss'])
plt.plot(hist.history['val_loss'])
plt.title('Grafik Plot Loss Model')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Test'], loc='upper right')
plt.show()

