# -*- coding: utf-8 -*-
"""TensorFlow-2.0-Notebook-3-Classifying Structured Data.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1kSMWOBUiuMXXPHeeXS1U2ZSYDF-cpbuo

### Importing TensorFlow and dependencies
"""

# Commented out IPython magic to ensure Python compatibility.
# %%time 
# from __future__ import absolute_import, print_function, division, unicode_literals
# 
# import numpy as np
# import pandas as pd
# 
# try:
#   %tensorflow_version 2.x
#   print("TensorFlow is up and running.")
# except:
#   print("TensorFlow NOT FOUND.")
# 
# import tensorflow as tf
# from tensorflow import feature_column
# from tensorflow.keras import layers
# from sklearn.model_selection import train_test_split
# 
# print("TensorFlow Version: ",tf.__version__)
# print("Eager Execution Enabled: ",tf.executing_eagerly())
# print("GPU is", "avaliable" if tf.test.is_gpu_available() else "not available")
# 
# import warnings
# warnings.filterwarnings("ignore")
# 
# print("Done.!")

"""### Loading the Dataset"""

URL = 'https://storage.googleapis.com/applied-dl/heart.csv'
df_raw = pd.read_csv(URL)
df_raw.head()

train, test = train_test_split(df_raw, test_size=0.2)
train, val = train_test_split(train, test_size=0.2)
print(len(train),"Train Samples.")
print(len(test),"Test Samples.")
print(len(val),"Validation Samples.")

"""### Create an Input Pipeline using tf.data

Next, we will wrap the dataframes with tf.data. This will enable us to use feature columns as a bridge to map from the columns in the Pandas dataframe to features used to train the model. If we were working with a very large CSV file (so large that it does not fit into memory), we would use tf.data to read it from disk directly. That is not covered in this tutorial.
"""

def df_to_dataset(dataframe, shuffle=True, batch_size=32):
  dataframe = dataframe.copy()
  labels = dataframe.pop('target')
  ds = tf.data.Dataset.from_tensor_slices((dict(dataframe),labels))
  if shuffle:
    ds = ds.shuffle(buffer_size=len(dataframe))
  ds = ds.batch(batch_size)
  return ds

batch_size = 5
train_ds = df_to_dataset(train, batch_size=batch_size)
val_ds = df_to_dataset(val, shuffle=False, batch_size=batch_size)
test_ds = df_to_dataset(test, shuffle=False, batch_size=batch_size)

for feature_batch, label_batch in train_ds.take(1):
  print("Every feature: ", list(feature_batch.keys()))
  print("A batch of ages: ", feature_batch['age'])
  print("A batch of targets: ",label_batch)

"""### Demonstrate several types of feature column

TensorFlow provides many types of feature columns. In this section, we will create several types of feature columns, and demonstrate how they transform a column from the dataframe.
"""

example_batch = next(iter(train_ds))[0]

def demo(feature_column):
  feature_layer = layers.DenseFeatures(feature_column)
  print(feature_layer(example_batch).numpy())

"""#### Numeric Columns"""

age = feature_column.numeric_column("age")
demo(age)

"""#### Bucketized Columns"""

age_buckets = feature_column.bucketized_column(age, boundaries=[18, 25, 30, 35, 40, 45, 50, 55, 60, 65])
demo(age_buckets)

"""#### Categorical Columns"""

thal = feature_column.categorical_column_with_vocabulary_list(
    'thal', ['fixed','normal','reversible']
)

thal_one_hot = feature_column.indicator_column(thal)

demo(thal_one_hot)

"""#### Embedding Column"""

thal_embedding = feature_column.embedding_column(thal,dimension=8)
demo(thal_embedding)

"""#### Hashed feature column"""

thal_hashed = feature_column.categorical_column_with_hash_bucket(
    'thal', hash_bucket_size=1000
)
demo(feature_column.indicator_column(thal_hashed))

"""#### Crossed feature column"""

crossed_feature = feature_column.crossed_column([age_buckets, thal], hash_bucket_size=1000)
demo(feature_column.indicator_column(crossed_feature))

"""### Choosing columns to use

We have seen how to use several types of feature columns. Now we will use them to train a model. The goal of this tutorial is to show you the complete code (e.g. mechanics) needed to work with feature columns. We have selected a few columns to train our model below arbitrarily.

Key point: If your aim is to build an accurate model, try a larger dataset of your own, and think carefully about which features are the most meaningful to include, and how they should be represented.
"""

feature_columns = []

for header in ['age', 'trestbps', 'chol', 'thalach', 'oldpeak', 'slope', 'ca']:
  feature_columns.append(feature_column.numeric_column(header))

feature_columns

age_buckets = feature_column.bucketized_column(age, boundaries=[10,25,35,40,50,55,60,65])
feature_columns.append(age_buckets)

thal = feature_column.categorical_column_with_vocabulary_list(
    'thal', ['fixed','normal','reversible']
)
thal_one_hot = feature_column.indicator_column(thal)
feature_columns.append(thal_one_hot)

thal_embedding = feature_column.embedding_column(thal, dimension=8)
feature_columns.append(thal_embedding)

crossed_feature = feature_column.crossed_column([age_buckets, thal],hash_bucket_size=1000)
crossed_feature = feature_column.indicator_column(crossed_feature)
feature_columns.append(crossed_feature)

feature_columns

feature_layer = tf.keras.layers.DenseFeatures(feature_columns)

batch_size = 32
train_ds = df_to_dataset(train, batch_size=batch_size)
val_ds = df_to_dataset(val, shuffle=False, batch_size=batch_size)
test_ds = df_to_dataset(test, shuffle=False, batch_size=batch_size)

demo(feature_columns)

model = tf.keras.Sequential([
                            feature_layer,
                            layers.Dense(256, activation="relu",kernel_initializer="glorot_uniform"),
                            layers.Dropout(0.2),
                            layers.BatchNormalization(),
                            layers.Dense(128, activation="relu",kernel_initializer="glorot_uniform"),
                            layers.Dropout(0.2),
                            layers.BatchNormalization(),
                            layers.Dense(64, activation="relu",kernel_initializer="glorot_uniform"),
                            layers.Dropout(0.2),
                            layers.Dense(1, activation="sigmoid")
])

model.compile(optimizer="adam",
              loss='binary_crossentropy',
              metrics=["accuracy"],
              run_eagerly=True)

reduce_lr_plateau = tf.keras.callbacks.ReduceLROnPlateau(mode="auto",verbose=1,patience=2,monitor="val_loss",factor=0.5)
checkpoint = tf.keras.callbacks.ModelCheckpoint("model_classify.h5",verbose=1,save_best_only=True,mode="auto",monitor="val_loss")
early_stopping = tf.keras.callbacks.EarlyStopping(mode="auto",patience=15,verbose=1,monitor="val_loss")

history = model.fit(train_ds, validation_data=val_ds,epochs=50,callbacks=[reduce_lr_plateau, checkpoint, early_stopping])

results = model.evaluate(test_ds)
for value, result in zip(model.metrics_names,results):
  print("%s:%.2f"%(value, result))

history_df = pd.DataFrame(history.history)
history_df["epochs"] = history.epoch
history_df.head(3)

# Commented out IPython magic to ensure Python compatibility.
import matplotlib.pyplot as plt
# %matplotlib inline
# %config InlineBackend.figure_format = "retina"
import seaborn as sns
sns.set(rc={"figure.figsize":(12,10)})
sns.set_style("whitegrid")

def plot(history):
  plt.subplot(2,1,1)
  plt.plot(history["epochs"],history["loss"],marker='o',label="training")
  plt.plot(history["epochs"],history["val_loss"],marker='o',label="validation")
  plt.xlabel("Epochs")
  plt.ylabel("Loss")
  plt.grid(True)
  plt.legend()
  plt.title("Loss Graph")
  plt.show()

  plt.subplot(2,1,2)
  plt.plot(history["epochs"],history["accuracy"],marker='o',label="training")
  plt.plot(history["epochs"],history["val_accuracy"],marker='o',label="validation")
  plt.xlabel("Epochs")
  plt.ylabel("Accuracy")
  plt.grid(True)
  plt.legend()
  plt.title("Accuracy Graph")
  plt.show()

plot(history_df)