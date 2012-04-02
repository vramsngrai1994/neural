#!/usr/bin/env python
from functools import partial

import scipy
import numpy as np

import display_network
import sample_images
import numerical_gradient

np.seterr('raise')

def norm(x):
    """Accepts n-d array. Calculates L2-norm.
        Returns real.
    """
    return np.sqrt(np.sum(x**2))


def softmax_cost(theta, num_classes, input_size, weight_decay, data, labels):
    """
    % num_classes - the number of classes 
    % input_size - the size N of the input vector
    % weight_decay - weight decay parameter
    % data - the N x M input matrix, where each column data(:, i) corresponds to
    %        a single test set
    % labels - an M x 1 matrix containing the labels corresponding for the input data
    """
    # Unroll the parameters from theta
    theta = theta.reshape((num_classes, input_size))
    num_data = data.shape[1]
    assert theta.shape == (num_classes, input_size)

    assert data.shape == (input_size, num_data)
    # efficiently build large sparse matrix
    ij = np.array([[i, l] for i,l in enumerate(labels)]).T
    ground_truth = scipy.sparse.coo_matrix((np.ones(num_data), ij),
                                shape=(num_data, num_classes)).todense().T
    assert ground_truth.shape == (num_classes, num_data)

    # calculate cost function
    full_prediction = np.dot(theta, data)
    max_prediction = np.max(full_prediction, axis=0)
    shrunk_prediction = full_prediction - max_prediction
    exp_shrunk_prediction = np.exp(shrunk_prediction) 
    prediction = (exp_shrunk_prediction / 
                                    np.sum(exp_shrunk_prediction, axis=0))
    assert full_prediction.shape == (num_classes, num_data)
    assert max_prediction.shape == (num_data,)
    assert shrunk_prediction.shape == (num_classes, num_data)
    assert exp_shrunk_prediction.shape == (num_classes, num_data)
    assert prediction.shape == (num_classes, num_data)

    log_term = np.log(prediction)
    cost = -1 * np.sum(np.multiply(ground_truth, log_term)) / num_data
    cost += (0.5 * weight_decay) * np.sum(theta**2)
    # done calculating cost function

    # calculate gradient of cost function
    theta_grad = np.zeros(theta.shape)

    #import pdb; pdb.set_trace()
    for j in xrange(num_classes):
        row = np.zeros((input_size,))
        for i in xrange(num_data):
            row += data[:,i] * (ground_truth[j, i] - prediction[j, i])
        assert row.shape == (input_size,)
        theta_grad[j] += row * -1.0 / num_data
    theta_grad += weight_decay * theta
    assert theta_grad.shape == theta.shape

    return cost, np.array(theta_grad).flatten()


def softmax_train(input_size, num_classes, weight_decay, data, labels, max_iter):
    """
    % softmaxTrain Train a softmax model with the given parameters on the given
    % data. Returns softmaxOptTheta, a vector containing the trained parameters
    % for the model.
    %
    % input_size: the size of an input vector x^(i)
    % num_classes: the number of classes 
    % weight_decay: weight decay parameter
    % input_data: an N by M matrix containing the input data, such that
    %            inputData(:, c) is the cth input
    % labels: M by 1 matrix containing the class labels for the
    %            corresponding inputs. labels(c) is the class label for
    %            the cth input
    %  max_iter: number of iterations to train for
    """
    # initialize parameters
    theta = 0.005 * np.random.randn(num_classes * input_size)

    sc = lambda x: softmax_cost(x, num_classes, 
                                   input_size, 
                                   weight_decay, 
                                   data, 
                                   labels)

    # Train!
    trained, cost, d = scipy.optimize.lbfgsb.fmin_l_bfgs_b(sc, theta,
                                                           maxfun=max_iter,
                                                           m=100,
                                                           factr=1.0,
                                                           pgtol=1e-100,
                                                           iprint=1)
    return trained.reshape((num_classes, input_size))


if __name__=='__main__':
    num_examples = 20

    '''
    train, valid, test = sample_images.load_mnist_images('data/mnist.pkl.gz')
    display_network.display_network('mnist.png', train[0].T[:,:num_examples])
    '''

    input_size = 28 * 28 # Size of input vector (MNIST images are 28x28)
    num_classes = 10     # Number of classes (MNIST images fall into 10 classes)
    weight_decay = 1e-4 # Weight decay parameter

    # for testing
    input_size = 8
    data = np.random.randn(input_size, num_examples)
    labels = np.random.randint(0, num_classes, num_examples)

    # do gradient calculations
    # check numerically

    theta = 0.005 * np.random.randn(num_classes * input_size)

    sc = partial(softmax_cost, num_classes=num_classes,
                               input_size=input_size,
                               weight_decay=weight_decay,
                               data=data,
                               labels=labels)

    cost, grad = sc(theta)

    ngrad = numerical_gradient.compute(theta,
                                       lambda x: sc(x)[0],
                                       epsilon=0.0001)
 
    try:
        print ngrad, grad
        diff = norm(grad-ngrad)/norm(grad+ngrad)
        print 'diff', diff
        assert diff < 2e-9
    except Exception, e:
        print e
        import pdb; pdb.post_mortem()
