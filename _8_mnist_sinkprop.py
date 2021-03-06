import theano
from theano import tensor as T
from theano.sandbox.rng_mrg import MRG_RandomStreams as RandomStreams
import numpy as np
from theano.tensor.nnet.conv import conv2d
from theano.tensor.signal.downsample import max_pool_2d
from lib import *

class DigitCNN():

    def __init__(self):


        X = T.fmatrix()
        Y = T.fmatrix()
        eta = T.scalar()
        perm_eta = T.scalar()
        drop_conv = T.scalar()
        drop_full = T.scalar()

        #self.pW = positive_weights((784, 784))
        self.pW = positive_weights((784,784))

        self.w = random_weights((32, 1, 3, 3))
        self.w2 = random_weights((64, 32, 3, 3))
        self.w3 = random_weights((128, 64, 3, 3))
        self.w4 = random_weights((128*3*3, 625))
        self.w_o = random_weights((625, 10))


        self.b_c1 = zeros(32)
        self.b_c2 = zeros(64)
        self.b_c3 = zeros(128)

        self.b_h1 = zeros(625)
        self.b_o  = zeros(10)

        p = T.dot(X, sinkprop(self.pW, num_iters=1))
        p2d = p.reshape((-1,1,28,28))

        l1_lin = conv2d(p2d, self.w, border_mode='full') + self.b_c1.dimshuffle('x', 0, 'x', 'x')
        l1a = rectify(l1_lin)
        l1 = max_pool_2d(l1a, (2, 2))
        l1 = dropout(l1, drop_conv)

        l2_lin = conv2d(l1, self.w2) + self.b_c2.dimshuffle('x', 0, 'x', 'x')
        l2a =  rectify(l2_lin)
        l2 = max_pool_2d(l2a, (2, 2))
        l2 = dropout(l2, drop_conv)

        l3_lin = conv2d(l2, self.w3) + self.b_c3.dimshuffle('x', 0, 'x', 'x')
        l3a = rectify(l3_lin)
        l3b = max_pool_2d(l3a, (2, 2))
        l3 = T.flatten(l3b, outdim=2)
        l3 = dropout(l3, drop_conv)

        l4_lin = T.dot(l3, self.w4) + self.b_h1
        l4 = rectify(l4_lin)
        l4 = dropout(l4, drop_full)

        yhat = softmax(T.dot(l4, self.w_o) + self.b_o )


        y_x = T.argmax(yhat, axis=1)


        cost = T.mean(T.nnet.categorical_crossentropy(yhat, Y))
        params = [self.w, self.w2, self.w3, self.w4, self.w_o,
                  self.b_c1, self.b_c2, self.b_c3, self.b_h1, self.b_o,
                ]
        perm_params = [self.pW]

        caches = make_caches(params)

        updates = SGD(cost, params, eta)
        updates += SGD_positive(cost, perm_params, perm_eta)


        self.shapes = theano.function(inputs=[X, drop_conv],outputs=[l1.shape, l2.shape, l3.shape], allow_input_downcast=True)

        self.train_func = theano.function(inputs=[X, Y, drop_conv, drop_full, eta, perm_eta], outputs=cost, updates=updates, allow_input_downcast=True)
        self.predict_func = theano.function(inputs=[X, drop_conv, drop_full], outputs=y_x, allow_input_downcast=True)

    def train(self, X, Y, drop_conv=.3, drop_full=.5, eta=.01, perm_eta=.01):
        return self.train_func(X, Y, drop_conv, drop_full, eta, perm_eta)

    def predict(self, X):
        return self.predict_func(X, 0., 0.)



