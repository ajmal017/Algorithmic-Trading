#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 16:47:24 2020

@author: josephgross
"""


# =============================================================================
# Data extraction from stockrow.com
# Author : Reza Sadegehi (Reviewed by Mayank Rasu)

# Please report bug/issues in the Q&A section
# =============================================================================
import pandas as pd 

from enum import Enum

tickers=["BA"] #list of tickers whose data needs to be extracted


class Financials(Enum):
    
    Income_Statement = 1
    Balanced_Sheet = 2
    CashFlow = 3
    Key_Metrics=4
    Growth=5

class Terms(Enum):
    Quarterly=1
    Annual=2
    Trailing=3


def FinFun(ticker,Fin,Term):
    """Please create the folder structure C:/Data-Stockrow/Income Statement in your local machine"""
    if Fin==Financials.Balanced_Sheet:
        if Term==Terms.Annual:
            URL="https://stockrow.com/api/companies/"+ticker+"/financials.xlsx?dimension=A&section=Income%20Statement&sort=desc"
            
            filename= "Income Statements/{}-AnnualIncome-Statement.csv".format(ticker)
            return URL, filename
        
        elif Term==Terms.Quarterly:
            URL="https://stockrow.com/api/companies/"+ticker+"/financials.xlsx?dimension=Q&section=Income%20Statement&sort=desc"
                     
            filename= "Income Statements/{}-QuartlyIncome-Statement.csv".format(ticker)
            return URL, filename   
        

        elif Term==Terms.Trailing:
            URL="https://stockrow.com/api/companies/"+ticker+"/financials.xlsx?dimension=T&section=Income%20Statement&sort=desc"
         
            filename= "Income Statements/{}-TrailingIncome-Statement.csv".format(ticker)
            return URL, filename   
        
        
        
def Download_data(ticker,Fin,Term):        
        

    URL,filename= FinFun(ticker ,Fin,Term)
    print(" Download "+ str(Fin) +" for stock: " + ticker + " terms : " +str(Term) )

    df= pd.read_excel(URL)
    
    #
    df.to_csv(filename,index=False)
    pd.read_csv(filename, header=None).T.to_csv(filename, header=False, index=False)
    
    
    df=pd.read_csv(filename,index_col=False   )
    
     # change the name of the columns 
    columns=df.columns.values.tolist()
    columns[0]="date"
    df.columns=columns
    
    #shorten the date and change the index to date
    df['date'] =pd.to_datetime(df["date"])
    df['date']  = df['date'].dt.date
    # save the file
    df.to_csv(filename,index=False)


for ticker in tickers:
    Download_data(ticker, Financials.Balanced_Sheet, Terms.Annual)
    Download_data(ticker, Financials.Balanced_Sheet, Terms.Quarterly)
    Download_data(ticker, Financials.Balanced_Sheet, Terms.Trailing)

