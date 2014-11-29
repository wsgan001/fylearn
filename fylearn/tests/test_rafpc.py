
import numpy as np
from sklearn.utils.testing import assert_equal, assert_true

import fylearn.rafpc as rafpc
    
def test_classifier():

    l = rafpc.RandomAgreementFuzzyPatternClassifier(n_agreeing = 2, n_samples = 1)

    X = np.array([
        [0.1,  0.2,  0.4],
        [0.15, 0.18, 0.43],
        [0.2,  0.4,  0.8 ],
        [0.25, 0.42, 0.78]
    ])

    y = np.array([
        0,
        0,
        1,
        1
    ])
    
    l.fit(X, y)

    assert_equal([0], l.predict([[0.9, 1.7, 4.5]]))

def test_classifier_single():

    l = rafpc.RandomAgreementFuzzyPatternClassifier(n_agreeing = 2, n_samples = 1)

    X = np.array([
        [0.1,  0.2,  0.4],
        [0.15, 0.18, 0.43],
        [0.2,  0.4,  0.8 ],
        [0.25, 0.42, 0.78]
    ])

    y = np.array([
        0,
        0,
        1,
        1
    ])
    
    l.fit(X, y)

    assert_equal(0, l.predict([0.9, 1.7, 4.5]))
        
        
def test_classifier_iris():

    import os
    csv_file = os.path.join(os.path.dirname(__file__), "iris.csv")
    data = np.genfromtxt(csv_file, dtype=float, delimiter=',', names=True)

    X = np.array([data["sepallength"], data["sepalwidth"], data["petallength"], data["petalwidth"]]).T
    y = data["class"]

    from sklearn.preprocessing import MinMaxScaler
    X = MinMaxScaler().fit_transform(X)

    l = rafpc.RandomAgreementFuzzyPatternClassifier(n_agreeing = 2, random_state = 0)

    from sklearn import cross_validation

    scores = cross_validation.cross_val_score(l, X, y, cv=10)
    mean = np.mean(scores)

    print "mean", mean

    assert_true(0.90 < mean)
    
