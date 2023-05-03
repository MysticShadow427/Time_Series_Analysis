# -*- coding: utf-8 -*-
"""RNN_Analysis.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1RHzbsoqwmIN5PEfpUdtq98tTGqk2pWzO

# Multivariate Time Series with RNN

Appliance Energy Usage:  Multivariate Time Series Forecasting

Experimental data used to create regression models of appliances energy use in a low energy building.
Data Set Information:

The data set is at 10 min for about 4.5 months. The house temperature and humidity conditions were monitored with a ZigBee wireless sensor network. Each wireless node transmitted the temperature and humidity conditions around 3.3 min. Then, the wireless data was averaged for 10 minutes periods. The energy data was logged every 10 minutes with m-bus energy meters. Weather from the nearest airport weather station (Chievres Airport, Belgium) was downloaded from a public data set from Reliable Prognosis (rp5.ru), and merged together with the experimental data sets using the date and time column. Two random variables have been included in the data set for testing the regression models and to filter out non predictive attributes (parameters).
Original source of the dataset:

http://archive.ics.uci.edu/ml/datasets/Appliances+energy+prediction
___
___
"""

# Commented out IPython magic to ensure Python compatibility.
import pandas as pd
import numpy as np
# %matplotlib inline
import matplotlib.pyplot as plt

"""## Data

Let's read in the data set:
"""

df = pd.read_csv('../DATA/energydata_complete.csv',index_col='date',
                infer_datetime_format=True)

df.head()

df.info()

df['Windspeed'].plot(figsize=(12,8))

df['Appliances'].plot(figsize=(12,8))

"""## Train Test Split"""

len(df)

df.head(3)

df.tail(5)

"""Let's imagine we want to predict just 24 hours into the future, we don't need 3 months of data for that, so let's save some training time and only select the last months data."""

df.loc['2016-05-01':]

df = df.loc['2016-05-01':]

"""Let's also round off the data, to one decimal point precision, otherwise this may cause issues with our network (we will also normalize the data anyways, so this level of precision isn't useful to us)"""

df = df.round(2)

len(df)

# How many rows per day? We know its every 10 min
24*60/10

test_days = 2

test_ind = test_days*144

test_ind

train = df.iloc[:-test_ind]
test = df.iloc[-test_ind:]

train

test

"""## Scale Data"""

from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()

scaler.fit(train)

scaled_train = scaler.transform(train)
scaled_test = scaler.transform(test)

"""# Time Series Generator

"""

from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator

# scaled_train

# define generator
length = 144 # Length of the output sequences (in number of timesteps)
batch_size = 1 #Number of timeseries samples in each batch
generator = TimeseriesGenerator(scaled_train, scaled_train, length=length, batch_size=batch_size)

len(scaled_train)

len(generator)

# What does the first batch look like?
X,y = generator[0]

print(f'Given the Array: \n{X.flatten()}')
print(f'Predict this y: \n {y}')

"""### Create the Model"""

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense,LSTM

scaled_train.shape

# define model
model = Sequential()

# Simple RNN layer
model.add(LSTM(100,input_shape=(length,scaled_train.shape[1])))

# Final Prediction (one neuron per feature)
model.add(Dense(scaled_train.shape[1]))

model.compile(optimizer='adam', loss='mse')

model.summary()

"""## EarlyStopping"""

from tensorflow.keras.callbacks import EarlyStopping
early_stop = EarlyStopping(monitor='val_loss',patience=1)
validation_generator = TimeseriesGenerator(scaled_test,scaled_test, 
                                           length=length, batch_size=batch_size)

model.fit_generator(generator,epochs=10,
                    validation_data=validation_generator,
                   callbacks=[early_stop])

model.history.history.keys()

losses = pd.DataFrame(model.history.history)
losses.plot()

"""## Evaluate on Test Data"""

first_eval_batch = scaled_train[-length:]

first_eval_batch

first_eval_batch = first_eval_batch.reshape((1, length, scaled_train.shape[1]))

model.predict(first_eval_batch)

scaled_test[0]

"""Now let's put this logic in a for loop to predict into the future for the entire test range.

----
"""

n_features = scaled_train.shape[1]
test_predictions = []

first_eval_batch = scaled_train[-length:]
current_batch = first_eval_batch.reshape((1, length, n_features))

for i in range(len(test)):
    
    # get prediction 1 time stamp ahead ([0] is for grabbing just the number instead of [array])
    current_pred = model.predict(current_batch)[0]
    
    # store prediction
    test_predictions.append(current_pred) 
    
    # update batch to now include prediction and drop first value
    current_batch = np.append(current_batch[:,1:,:],[[current_pred]],axis=1)

test_predictions

scaled_test

"""## Inverse Transformations and Compare"""

true_predictions = scaler.inverse_transform(test_predictions)

true_predictions

test

true_predictions = pd.DataFrame(data=true_predictions,columns=test.columns)

true_predictions

from tensorflow.keras.models import load_model

model.save("multivariate.h5")