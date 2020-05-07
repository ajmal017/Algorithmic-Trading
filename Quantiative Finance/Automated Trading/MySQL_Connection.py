#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 12:31:36 2020

@author: josephgross
"""


import mysql.connector
from mysql.connector import Error
    
    
def test_mysql_connection():

    try:
        db_host = '127.0.0.1'
        db_user = 'sec_user'
        db_password = 'UZHuYbneFK2'
        db_name = 'securities_master'
        #connection = mdb.connect(
        #    host=db_host, user=db_user, passwd=db_pass, db=db_name
        #)
        
        connection = mysql.connector.connect(
                                user=db_user, 
                                password=db_password,
                                host=db_host,
                                database=db_name)

        if connection.is_connected():
            db_Info = connection.get_server_info()
            print("Connected to MySQL Server version ", db_Info)
            cursor = connection.cursor()
            cursor.execute("select database();")
            record = cursor.fetchone()
            print("Your connected to database: ", record)
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

    except Error as e:
        print("Error while connecting to MySQL", e)
        

    
def test_table_creation():
   
    try:
        db_host = '127.0.0.1'
        db_user = 'sec_user'
        db_password = 'UZHuYbneFK2'
        db_name = 'securities_master'

        connection = mysql.connector.connect(
                                user=db_user, 
                                password=db_password,
                                host=db_host,
                                database=db_name)
        

        mySql_Create_Table_Query = """CREATE TABLE books ( 
                             title varchar(250) NOT NULL,
                             isbn varchar(250) NOT NULL,
                             date_created datetime NULL,
                             PRIMARY KEY (title)) """

        cursor = connection.cursor()
        cursor.execute(mySql_Create_Table_Query)
        print("Books Table created successfully ")

    except mysql.connector.Error as error:
        print("Failed to create table in MySQL: {}".format(error))
    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("MySQL connection is closed")
    
        
def test_truncate_table(table_name):
   
    try:
        db_host = '127.0.0.1'
        db_user = 'sec_user'
        db_password = 'UZHuYbneFK2'
        db_name = 'securities_master'

        connection = mysql.connector.connect(
                                user=db_user, 
                                password=db_password,
                                host=db_host,
                                database=db_name)

        cursor = connection.cursor()
        cursor.execute("TRUNCATE TABLE {}".format(table_name))

        print("{} Table truncated successfully".format(table_name))

    except mysql.connector.Error as error:
        print("Failed to truncate table in MySQL: {}".format(error))
    
    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("MySQL connection is closed")
  
          
            
def test_insert_book(books):
    import mysql.connector
    from mysql.connector import Error
    
    query = "INSERT INTO books(title,isbn) " \
            "VALUES(%s,%s)"
 
    try:
        db_host = '127.0.0.1'
        db_user = 'sec_user'
        db_password = 'UZHuYbneFK2'
        db_name = 'securities_master'

        conn = mysql.connector.connect(
                                user=db_user, 
                                password=db_password,
                                host=db_host,
                                database=db_name)
 
        cursor = conn.cursor()
        cursor.executemany(query, books)
        
        conn.commit()
        
    except Error as error:
        print(error)
 
    finally:
        cursor.close()
        conn.close()

def get_sample_books():
    books = [('Harry Potter And The Order Of The Phoenix', '9780439358071'),
             ('Gone with the Wind', '9780446675536'),
             ('Pride and Prejudice (Modern Library Classics)', '9780679783268')]
    return books


if __name__ == "__main__":
    test_mysql_connection()
    
    print("=============================")
    
    #test_table_creation()
    #test_insert_book(get_sample_books())
    
    print("=============================")
    
    test_truncate_table("daily_price")
