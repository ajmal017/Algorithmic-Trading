#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 11 22:32:30 2020

@author: josephgross
"""

# Hit Rate: A percentage of the number of times a classifier correctly predicted
# the up or down direction


# Confusion Matrix: How many times did we predict up correctly and how many
# time did we predict down correctly? Did they differ substantially?
# (    Up_true       Up_false   )
# (    Down_false    Down_true  )






import datetime as dt
import numpy as np 
import pandas as pd 
import sklearn

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import (
    LinearDiscriminantAnalysis as LDA,
    QuadraticDiscriminantAnalysis as QDA)
from sklearn.metrics import confusion_matrix
from sklearn.svm import LinearSVC, SVC


from alpha_vantage.timeseries import TimeSeries


def get_daily_historic_data_alphavantage(ticker, start_date, end_date):
    """
    
    Use the generated API call to query AlphaVantage with the 
    appropriate API key and return a list of price tuples for 
    a particular ticker

    Parameters
    ----------
    ticker : 'str'
        The ticker of a stock which will be used to retrieve price data
        from alpha_vantage

    Returns
    -------
    'list'
            List of tuples with historical price data based on a 
            specific ticker

    """
    
    ALPHA_VANTAGE_API_KEY = 'YZZ4PFN9ATU1ASPAN'
    COLUMNS = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
    
    try:
        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='json')
        data, meta_data = ts.get_daily_adjusted(symbol=ticker, outputsize='full')
    except Exception as e:
        print(
            "Could not download AlphaVantage data for %s ticker "
            "(%s)...skipping." % (ticker, e)
        )
        return []
    else:
        prices = []
        
        for date_str in sorted(data.keys()):
            date = dt.datetime.strptime(date_str, '%Y-%m-%d') 
            if date < start_date or date > end_date:
                continue
            
            bar = data[date_str]
            prices.append(
                (
                    date_str,
                    float(bar['1. open']),
                    float(bar['2. high']),
                    float(bar['3. low']),
                    float(bar['4. close']),
                    int(bar['6. volume']),
                    float(bar['5. adjusted close'])
                )
            )
    
    return pd.DataFrame(prices, columns=COLUMNS).set_index('Date')


def create_lagged_series(symbol, start_date, end_date, lags=5):
    """
    This creates a Pandas DataFrame that stores the percentage of the 
    adjusted closing value of a stock obtained from AlphaVantage, along 
    with a number of lagged returns from the prior trading days (default is 5).
    Training Volume as well as the direction from the previous day are also
    included

    Parameters
    ----------
    symbol : 'str'
        The ticker symbol to obtain from AlphaVantage
    start_date : 'datetime'
        The starting date of the series to obtain
    end_date : 'datetime'
        The ending date of the series to obtain
    lags : 'int', optional
        The number of days to 'lag' the series by. The default is 5.

    Returns
    -------
    'pd.DataFrame'
        Contains the Adjusted Closing Price returns and lags

    """
    
    # Obtain stock pricing from AlphaVantage
    adj_start_date = start_date - dt.timedelta(days=365)
    ts = get_daily_historic_data_alphavantage(symbol, adj_start_date, end_date)
    ts.index = pd.to_datetime(ts.index)
    
    
    # Create the new lagged DataFrame
    tslag = pd.DataFrame(index=ts.index)
    tslag['Today'] = ts['Adj Close']
    tslag['Volume'] = ts['Volume']
    
    
    # Create the shifted lag series of prior trading period close values
    for i in range(0, lags):
        tslag['Lag%s' % str(i+1)] = ts["Adj Close"].shift(i+1)
        
    # Create the returns DataFrame
    tsret = pd.DataFrame(index=tslag.index)
    tsret['Volume'] = tslag['Volume']
    tsret['Today']  = tslag['Today'].pct_change() * 100
    
    
    # If any of the values of percentage returns equal zero, set them to 
    # a small number (stops issues with the QDA model in scikit-learn)
    tsret.loc[tsret['Today'].abs() < 0.0001, ['Today']] = 0.0001
    
    # Create the lagged percentage returns columns
    for i in range(0, lags):
        tsret['Lag%s' % str(i+1)] = \
            tslag['Lag%s' % str(i+1)].pct_change() * 100
    
    
    # Create the "Direction" column (+1 or -1) indicating an up/down day
    tsret['Direction'] = np.sign(tsret['Today'])
    tsret = tsret[tsret.index >= start_date]
    
    return tsret



if __name__ == "__main__":
    
    # Download the S&P500 ETF time series
    start_date = dt.datetime(2016, 1, 10)
    end_date = dt.datetime(2017, 12, 31)
    
    # Create a lagged series of the S&P 500 US stock market index ETF
    snpret = create_lagged_series('SPY', start_date, end_date, lags=5)
    
    # Use the previous two days of return as predictor
    X = snpret[['Lag1', 'Lag2']]
    y = snpret['Direction']
    
    # The test data is split into two parts: Before and after 1st Jan 2017
    start_test = dt.datetime(2017, 1, 1)
    
    # Create training and test sets
    X_train = X[X.index < start_test]
    X_test = X[X.index >= start_test]
    y_train = y[y.index < start_test]
    y_test = y[y.index >= start_test]
    
    
    # Create the (parametrised) models
    print("Hit Rates / Confusion Matrices:\n")
    models = [
        ('LR', LogisticRegression(solver='liblinear')),
        ('LDA', LDA(solver='svd')),
        ('QDA', QDA()),
        ('LSVC', LinearSVC(max_iter=10000)),
        ('RVSM', SVC(
            C=1000000.0, cache_size=200, class_weight=None,
            coef0=0.0, degree=3, gamma=0.0001, kernel='rbf',
            max_iter=-1, probability=False, random_state=None,
            shrinking=True, tol=0.001, verbose=False)
        ),
        ('RF', RandomForestClassifier(
            n_estimators=1000, criterion='gini', max_depth=None,
            min_samples_split=2, min_samples_leaf=1, max_features='auto',
            bootstrap=True, oob_score=False, n_jobs=1, random_state=None,
            verbose=0)
        )
    ]
    
    
    # Iterate through the models
    for m in models:
        # Train each of the models on the training set
        m[1].fit(X_train, y_train)
        
        # Make an array of predictions on the test set
        pred = m[1].predict(X_test)
        
        # Output the hit-rate and the confusion matrix for each model
        print('%s:\n%0.3f' % (m[0], m[1].score(X_test, y_test)))
        print('%s\n' % confusion_matrix(pred, y_test))
    
    
    
    
    
    
    
    