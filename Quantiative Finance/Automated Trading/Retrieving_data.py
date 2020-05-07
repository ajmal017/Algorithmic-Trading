#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 19:20:19 2020

@author: josephgross
"""


import pandas as pd
import mysql.connector

if __name__ == "__main__":
    
    # Connect to the MySQL instance
    db_host = '127.0.0.1'
    db_user = 'sec_user'
    db_password = 'UZHuYbneFK2'
    db_name = 'securities_master'
    con = mysql.connector.connect(
                        user=db_user, 
                        password=db_password,
                        host=db_host,
                        database=db_name)
    
    # Select all of the historic Activision Blizzard adjusted close data
    sql_query = """SELECT dp.price_date, dp.adj_close_price
                FROM symbol as sym
                INNER JOIN daily_price AS dp
                ON dp.symbol_id = sym.id
                WHERE sym.ticker = 'ATVI'
                ORDER BY dp.price_date ASC; """
    
    # Create a pandas dataframe from the SQL query
    atvi = pd.read_sql_query(sql_query, con=con, index_col='price_date')
    
    # Output the dataframe tail
    print(atvi.tail())