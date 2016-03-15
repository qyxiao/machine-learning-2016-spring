import numpy as np
import pandas as pd

def getSummary(df):
    '''
    Messy code I wrote last semester.  
    Produces a DataFrame to summarize the input data DataFrame

    Args:
        df: a data frame, doesn't matter what's in from_items

    Returns:
        summary dataframe.  For each column it will provide:
            null count
            distinct value count
            top 10 most frequently-occuring values if there are fewer than 100 unique valueSeries
            data type

        also it prints out the shape of the DataFrame
    '''
    uniqueList = []
    typeList = []
    valueList = []
    iList = []
    meanList = []
    mean_rejList = []
    mean_appList = []
    
    for i,col in enumerate(df.columns):
        uniques = len(df[col][df[col].notnull()].unique())
        uniqueList.append(uniques)
        if(uniques>100):
            values = "too many to calculate"
        else:
            numvals = len(df[col].value_counts())
            values = df[col].value_counts().iloc[:min(10,numvals)]
        valueList.append(values)
        typeList.append(np.dtype(df[col]))
        iList.append(i)
        
    uniqueSeries = pd.Series(uniqueList, index=df.columns)
    valueSeries = pd.Series(valueList, index=df.columns)
    typeSeries = pd.Series(typeList, index=df.columns)
    iSeries = pd.Series(iList,index=df.columns)
    
    #uniques
    summaryItems = [
        ('nulls', df.shape[0] - df.count()),
        ('distinct_count', uniqueSeries),
        ('top10Values', valueSeries),
        ('dtype', typeSeries),
        ('i', iSeries)
    ]
    summaryDF = pd.DataFrame.from_items(summaryItems)
    print 'Rows,Columns',df.shape
    return summaryDF