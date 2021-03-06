import numpy as np
import tensorflow as tf
import utils
import math

BATCHSIZE = 10000
K = 5
MAX_ITER = 100
LR = 0.1
COLOR_LIST = ['r', 'g', 'b', 'm', 'y', 'k']
IS_VALID = False

# data = np.load('data/data2D.npy')
data = np.load('data/data100D.npy')
print(data.shape)
DIM = data.shape[1]
NUM_PTS = data.shape[0]
NUM_VALID = int(math.floor(NUM_PTS / 3.0))

if IS_VALID:
  npr = np.random.RandomState(1234)  
  data_idx = npr.permutation(NUM_PTS)
  val_data = data[data_idx[:NUM_VALID]] 
  data = data[data_idx[NUM_VALID:]] 

def DistFunc(X, Y):
  return -(tf.matmul(X, Y, transpose_b=True) * 2 - tf.reduce_sum(
      tf.square(tf.transpose(Y)), 0, keep_dims=True) - tf.reduce_sum(
          tf.square(X), 1, keep_dims=True))


def KmeansObjFunc(X, mu):

  dist = DistFunc(X, mu)
  label = tf.argmin(dist, axis=1)
  obj = tf.reduce_sum(
      tf.gather_nd(dist,
                   tf.pack(
                       [tf.range(tf.shape(X)[0]), tf.cast(label, tf.int32)],
                       axis=1)))

  return obj, label


graph = tf.Graph()
with graph.as_default():
  inputPL = tf.placeholder(tf.float32, shape=(None, DIM))

  ## Initialization
  mu = tf.Variable(tf.truncated_normal([K, DIM]) * 0.1)

  ## compute the log prob and posterior
  loss, label = KmeansObjFunc(inputPL, mu)

  optimizer = tf.train.AdamOptimizer(
      LR, beta1=0.9, beta2=0.99, epsilon=1e-5).minimize(loss)

train_loss = []

with tf.Session(graph=graph) as session:
  tf.global_variables_initializer().run()
  print('Initialized')
  for i in range(MAX_ITER):
    _, loss_np, mu_np, label_np = session.run(
        [optimizer, loss, mu, label], feed_dict={inputPL: data})

    print('Iter {:07d}: loss = {}'.format(i + 1, loss_np))
    train_loss += [loss_np]

    # save visualization
    if (i + 1) % 10 == 0 or i == 0:
      import pylab as plt
      plt.figure()
      percent = np.zeros(K)
      handles = []

      for ii in xrange(K):
        idx = label_np == ii
        percent[ii] = np.sum(idx.astype(np.float32)) / len(label_np)
        handles += [plt.scatter(data[idx, 0], data[idx, 1], c=COLOR_LIST[ii % len(COLOR_LIST)])]
        plt.scatter(mu_np[ii, 0], mu_np[ii, 1], marker='s', c='c', s=80)

      plt.legend(handles, percent)
      plt.savefig('figures/kmeans_{:07d}.png'.format(i + 1))

  if IS_VALID:
    loss_np = session.run([loss], feed_dict={inputPL: val_data})
    print("Validation loss = {}".format(loss_np[0]))

  # save loss function
  plt.figure()
  ax = plt.subplot(111)
  plt.plot(train_loss)
  ax.set_xlabel('Iteration')
  ax.set_ylabel('Training Loss')
  plt.savefig('figures/kmeans_train_loss.png')
