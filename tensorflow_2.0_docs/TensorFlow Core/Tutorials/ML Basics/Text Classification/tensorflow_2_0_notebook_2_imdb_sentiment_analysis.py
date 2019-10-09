# -*- coding: utf-8 -*-
"""Tensorflow-2.0-Notebook-2-IMDB-Sentiment-Analysis.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Zf1_83cTxiDSF_pER4KYiaW1XZHkLugU
"""

# Commented out IPython magic to ensure Python compatibility.
from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np

try:
  # %tensorflow_version only exists in Colab.
#   %tensorflow_version 2.x
except Exception:
  pass
import tensorflow as tf

import tensorflow_hub as hub
import tensorflow_datasets as tfds

print("Version: ", tf.__version__)
print("Eager mode: ", tf.executing_eagerly())
print("Hub version: ", hub.__version__)
print("GPU is", "available" if tf.test.is_gpu_available() else "NOT AVAILABLE")

train_validation_split = tfds.Split.TRAIN.subsplit([6, 4])

(train_data, validation_data), test_data = tfds.load(
    name="imdb_reviews", 
    split=(train_validation_split, tfds.Split.TEST),
    as_supervised=True)

!ls

train_examples_batch, train_labels_batch = next(iter(train_data.batch(10)))
train_examples_batch

train_labels_batch

embedding = "https://tfhub.dev/google/tf2-preview/gnews-swivel-20dim/1"

hub_layer = hub.KerasLayer(embedding, input_shape=[],
                           dtype=tf.string, trainable=True)

hub_layer(train_examples_batch[:3])

model = tf.keras.Sequential()
model.add(hub_layer)
model.add(tf.keras.layers.Dense(16, activation="relu"))
model.add(tf.keras.layers.Dense(1,activation="sigmoid"))
model.summary()

model.compile(optimizer="adam",loss="binary_crossentropy",metrics=["accuracy"])

reduce_lr_plateau = tf.keras.callbacks.ReduceLROnPlateau(mode="auto",monitor="val_loss",factor=0.3,patience=5,verbose=1,min_lr=0.00001)
checkpoint = tf.keras.callbacks.ModelCheckpoint("model_sentiment.h5",monitor="val_loss",verbose=1,save_best_only=True,mode="auto")
early_stopping = tf.keras.callbacks.EarlyStopping(monitor="val_loss",patience=5,verbose=1,mode="auto")

history = model.fit( train_data.shuffle(1000).batch(512), epochs=20, validation_data = validation_data.batch(512), verbose=1 , callbacks=[reduce_lr_plateau, checkpoint, early_stopping])

# Commented out IPython magic to ensure Python compatibility.
import matplotlib.pyplot as plt
# %matplotlib inline
# %config InlineBackend.figure_format = "retina"
import seaborn as sns
sns.set_style("whitegrid")
sns.set(rc={"figure.figsize":(12,10)})
import pandas as pd

history_df = pd.DataFrame(history.history)
history_df["epochs"] = history.epoch
history_df.head(3)

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

results = model.evaluate(test_data.batch(512),verbose=1)
for name, value in zip(model.metrics_names,results):
  print("%s: %.3f"%(name, value))