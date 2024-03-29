
import cv2
import time

import numpy as np
import tensorflow as tf

from Define import *
from Utils import *
from Conditional_GAN import *

# 1. load dataset
from tensorflow.examples.tutorials.mnist import input_data
mnist = input_data.read_data_sets(MNIST_DB_DIR, one_hot = True) #, reshape = []

print('[i] mnist train data : {}'.format(mnist.train.images.shape))
print('[i] mnist test data : {}'.format(mnist.test.images.shape))

# 2. build model
input_var = tf.placeholder(tf.float32, shape = [None, IMAGE_WIDTH * IMAGE_HEIGHT])
label_var = tf.placeholder(tf.float32, shape = [None, CLASSES])
z_var = tf.placeholder(tf.float32, shape = [None, HIDDEN_VECTOR_SIZE])

G_z = Generator(z_var, label_var, reuse = False)

D_real_logits, D_real = Discriminator(input_var, label_var, reuse = False)
D_fake_logits, D_fake = Discriminator(G_z, label_var, reuse = True)

# 3. loss
D_loss_real = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits = D_real_logits, labels = tf.ones([BATCH_SIZE, 1])))
D_loss_fake = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits = D_fake_logits, labels = tf.zeros([BATCH_SIZE, 1])))
D_loss_op = D_loss_real + D_loss_fake

G_loss_op = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits = D_fake_logits, labels = tf.ones([BATCH_SIZE, 1])))

# 4. select variables
vars = tf.trainable_variables()
D_vars = [var for var in vars if var.name.startswith('Discriminator')]
G_vars = [var for var in vars if var.name.startswith('Generator')]

# 5. optimizer
D_train_op = tf.train.AdamOptimizer(LEARNING_RATE, beta1 = 0.5).minimize(D_loss_op, var_list = D_vars)
G_train_op = tf.train.AdamOptimizer(LEARNING_RATE, beta1 = 0.5).minimize(G_loss_op, var_list = G_vars)

# 6. train
sess = tf.Session()
sess.run(tf.global_variables_initializer())

# get real data
real_images = (mnist.train.images - 0.5) / 0.5 # -1 ~ 1
real_labels = mnist.train.labels

# fixed vector
fixed_z = np.random.normal(0, 1, (SAVE_WIDTH * SAVE_HEIGHT, HIDDEN_VECTOR_SIZE))
fixed_y = []
for i in range(SAVE_HEIGHT):
    for j in range(SAVE_WIDTH):
        fixed_y.append(one_hot(i, CLASSES))

train_iteration = len(real_images) // BATCH_SIZE
    
for epoch in range(1, MAX_EPOCH + 1):
    st_time = time.time()

    G_loss_list = []
    D_loss_list = []

    for iter in range(train_iteration):
        # Discriminator
        batch_x = real_images[iter * BATCH_SIZE : (iter + 1) * BATCH_SIZE]
        batch_y = real_labels[iter * BATCH_SIZE : (iter + 1) * BATCH_SIZE]
        batch_z = np.random.normal(0, 1, (BATCH_SIZE, HIDDEN_VECTOR_SIZE))

        _, D_loss = sess.run([D_train_op, D_loss_op], {input_var : batch_x, label_var : batch_y, z_var : batch_z})
        D_loss_list.append(D_loss)

        # Generator
        batch_z = np.random.normal(0, 1, (BATCH_SIZE, HIDDEN_VECTOR_SIZE))

        batch_y = []
        batch_label = np.random.randint(0, 9, (BATCH_SIZE))
        
        for label in batch_label:
            y = one_hot(label, CLASSES)
            batch_y.append(y)
        
        batch_y = np.asarray(batch_y, dtype = np.float32)

        _, G_loss = sess.run([G_train_op, G_loss_op], {z_var : batch_z, label_var : batch_y})
        G_loss_list.append(G_loss)

    G_loss = np.mean(G_loss_list)
    D_loss = np.mean(D_loss_list)

    print('[i] epoch : {}, G_loss : {:.5f}, D_loss : {:.5f}'.format(epoch, G_loss, D_loss))

    # test
    fake_images = sess.run(G_z, feed_dict = {z_var : fixed_z, label_var : fixed_y})
    Save(fake_images, './results/{}.jpg'.format(epoch))

