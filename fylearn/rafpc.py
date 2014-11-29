# -*- coding: utf-8 -*-
"""Random agreement Fuzzy Pattern Classifier method.

The module structure is the following:

- The "RandomAgreementFuzzyPatternClassifier" implements the model learning using the [1] algorithm.

References:

[1] Davidsen, 2014.
  
"""
import numpy as np
from numpy.random import RandomState
import scipy.stats as stats

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils import check_arrays, column_or_1d, array2d, check_random_state

import fylearn.fuzzylogic as fl

def agreement_t_test(a, b):
    """ Check agreement based on means of two samples, using the t-statistic. """
    means1, stds1 = np.nanmean(a, 0), np.nanstd(a, 0)
    means2, stds2 = np.nanmean(b, 0), np.nanstd(b, 0)

    t1, p1 = stats.ttest_1samp(b, means1)
    # t2, p2 = stats.ttest_1samp(a, means2)

    # select agreeing featurs (p <= 0.05)
    return p1 < 0.05

def fuzzify(A):
    # output for fuzzified values
    R = np.zeros((A.shape[0], A.shape[1] * 3))

    cmin, cmax, cmean = np.nanmin(A, 0), np.nanmax(A, 0), np.nanmean(A, 0)

    left = np.array([cmin - (cmax - cmin), cmin, cmax]).T
    middle = np.array([cmin, cmean, cmax]).T
    right = np.array([cmin, cmax, cmax + (cmax - cmin)]).T

    for i in range(A.shape[1]):
        f_l = fl.TriangularSet(*left[i])
        f_m = fl.TriangularSet(*middle[i])
        f_r = fl.TriangularSet(*right[i])
        R[:,(i*3)] = f_l(A[:,i])
        R[:,(i*3)+1] = f_m(A[:,i])
        R[:,(i*3)+2] = f_r(A[:,i])

    return R

def agreement_fuzzy(A, B):
    """ Calculate fuzzy agreement using mean values and euclidean distance.

    A  :  First sample
    B  :  Second sample
    """

    # avg values of samples (column wise)
    S_A, S_B = np.nanmean(A, 0), np.nanmean(B, 0)

    #d = np.abs(S_A - S_B)
    #hamming = 1.0 - np.mean(d)
    #return hamming, d

    d = (S_A - S_B) ** 2
    rmse = 1.0 - np.sqrt(np.mean(d))
    return rmse, 1.0 - d

def triangular_factory(*args):
    return fl.TriangularSet(args[0], args[1], args[2])
                
def build_memberships(X, idxs, factory):
    mins  = np.nanmin(X, 0)
    maxs  = np.nanmax(X, 0)
    means = np.nanmean(X, 0)
    return [ (i, factory(means[i] - ((maxs[i] - mins[i]) / 2.0), means[i], means[i] + ((maxs[i] - mins[i]) / 2.0))) for i in idxs ]

class RandomAgreementFuzzyPatternClassifier(BaseEstimator, ClassifierMixin):

    def get_params(self, deep=False):
        return {"aggregation": self.aggregation,
                "n_agreeing": self.n_agreeing,
                "n_samples": self.n_samples,
                "sample_length": self.sample_length,
                "epsilon": self.epsilon,
                "membership_factory": self.membership_factory,
                "random_state": self.random_state}

    def set_params(self, **kwargs):
        for key, value in params.items():
            self.setattr(key, value)
        return self
    
    def __init__(self, n_samples=10, sample_length=100,
                 aggregation=fl.mean, membership_factory=triangular_factory,
                 n_agreeing=5, epsilon=0.8, 
                 random_state=None):
        """
        Initialize the classifier

        Parameters:
        -----------
        n_samples : the number of samples to draw for finding agreement

        sample_length : the length of each sample. If <1.0 then treat as a percentage.
                        If >=1.0 then treat as an absolute number.
        
        """
        self.n_samples = n_samples
        self.n_agreeing = n_agreeing
        self.sample_length = sample_length
        self.aggregation = aggregation
        self.membership_factory = membership_factory
        self.epsilon = epsilon
        self.random_state = random_state
    
    def fit(self, X, y):

        # get random
        rs = RandomState(self.random_state)

        X = array2d(X)
        
        X, y = check_arrays(X, y)
        n = len(X)

        self.classes_, y = np.unique(y, return_inverse=True)

        if np.nan in self.classes_:
            raise Exception("NaN not supported in class values")

        # agreeing not set, require all features to be in agreement
        if self.n_agreeing is None:
            self.n_agreeing = X.shape[1]

        if self.n_agreeing > X.shape[1]:
            raise Exception("Number of agreeing features must be less than/equal to number features in X")

        # build membership functions for each feature for each class
        self.protos_ = {}
        for class_idx, class_value in enumerate(self.classes_):
            X_class = X[y == class_idx]

            self.protos_[class_idx] = []
            for x in range(self.sample_length):
                #
                sample = X_class[rs.permutation(len(X_class))[:self.n_samples * 2]]
                sample1, sample2 = sample[:self.n_samples], sample[self.n_samples:]
                #
                agreement, d = agreement_fuzzy(sample1, sample2)

                ranking = np.argsort(1.0 - d)

                ranking = ranking[:self.n_agreeing]
                lastrank = d[ranking[-1]]

                # we need at least epsilon agreement of the features
                if lastrank >= self.epsilon:
                    self.protos_[class_idx].append(build_memberships(sample, ranking,
                                                                self.membership_factory))
        return self

    def predict(self, X):

        if self.protos_ is None:
            raise Exception("Prototypes not initialized. Perform a fit first.")

        X = array2d(X)

        Mus = np.zeros(X.shape) # holds output per prototype
        
        R = np.zeros((X.shape[0], len(self.classes_))) # holds output for each class

        agreement_nos = range(self.n_agreeing)

        # class_idx has class_prototypes membership functions
        for class_idx, class_prototypes in self.protos_.items():
            C = np.zeros((X.shape[0], len(class_prototypes)))
            for j, cp in enumerate(class_prototypes):
                for i in agreement_nos:
                    f_idx, f_f = cp[i]
                    Mus[:,i] = f_f(X[:,f_idx])
                C[:,j] = self.aggregation(Mus)
            R[:,class_idx] = np.max(C, 1)

        return self.classes_.take(np.argmax(R, 1))
