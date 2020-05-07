#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  4 22:00:05 2020

@author: josephgross
"""


import datetime 
import time

from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import ibConnection, message

from event import FillEvent
from execution import ExecutionHandler


class IBExecution(ExecutionHandler):
    """
    Handles order execution via the Interactive Brokers API,
    for use against accounts whent trading live directly.
    
    This class will receive OrderEvent instances from the events
    queue and then execute them directly against the Interactive
    Brokers order API. This class will also handle the "Server
    Response" messages sent back via the API.
    
    IMPORTANT:
        In order to start live trading, a new dataHandler 
        must be created to deal with a live market feed, 
        in order to replace the historical data feed handler 
        of the backtester system.
    
    """
    
    def __init__(self, events, order_routing="SMART", currency="USD"):
        """
        Initializes the IBExecutionHandler instance.


        Returns
        -------
        None.

        """        
        
        self.events = events
        self.order_routing = order_routing
        self.currency = currency
        self.fill_dict = {}
        
        self.tws_conn = self.create_tws_connection()
        self.order_id = self.create_initial_order_id()
        self.register_handlers()
        
        
    def error_handler(self, msg):
        """
        Handles the capturing of error messages.
        
        This method handles the ouput of the error messages
        to the terminal.
        

        Returns
        -------
        None.

        """
        
        # Currently no erro handling
        print("Server Error: %s" % msg)
        
    
    def _reply_handler(self, msg):
        """
        Handles the server replies.
        
        This method is used to determine if a FillEvent instance 
        needs to be created. The method asks if an "openOrder"
        message has been received and checks whether an entry in 
        the fill_dict for this particular orderId has already been set.
        If not, then one is created.
        

        Returns
        -------
        None.

        """
        
        # Handle open order orderId processing
        if (msg.typeName == "openOrder" and msg.orderId == self.order_id and
            not self.fill_dict.has_key(msg.orderId)):
            
            self.create_fill_dict_entry(msg):
        
        # Handle Fills
        if msg.typeName == "orderStatus" and msg.status == "Filled" and \
            self.fill_dict[msg.orderId]["filled"] == False:
                self.create_fill(msg)
                
        print("Server Response: %s, %s\n" % (msg.typeName, masg))
        
        
    def create_tws_connection(self):
        """
        Connect to the Trader Workstation (TWS) running on the usual
        port of 7496, with a clientId of 10. 
        
        The clientId is chosen by us and we will need seperate IDs for
        botht the execution connection and market data connection, if the
        latter is used elsewhere.

        Returns
        -------
        None.

        """
        
        tws_conn = ibConnection()
        tws_conn.connect()
        return tws_conn
    
    
    def create_initial_order_id(self):
        """
        Creates the initial order ID used for Interactive Brokers to 
        keep track of submitted orders.
        
        This has been defaulted to "1", but a more sophisticated
        approach would be to query IB for the latest abailable ID
        and use that.
        
        You can always reset the current API order ID via the Trader
        Workstation > Global Configuration > API Settings panel.

        Returns
        -------
        None.

        """                
        
        # There is scope fro more logic here but for now
        # we will use "1" as the default value
        
        return 1
    
    
    def register_handlers(self):
        """
        Register the error and server reply message handling functions.
        
        This method simply registers the error and reply handler methods
        defined earlier with the TWS connection.

        Returns
        -------
        None.

        """
        
        # Assign the error and server reply message handling functions
        self.tws_conn.register(self._error_handler, 'Error')
        
        # Assign all of the server reply messages to the reply_handler
        # function defined earlier.
        self.tws_conn.registerAll(self._reply_handler)
        
        
    def create_contract(self, symbol, sec_type, exch, prim_exch, curr):
        """
        Create a Contract object defining what will be purchased, 
        at which exchange and in which currency.
        
        In order to actually transact a trade, it is necessary to create
        an IbPy Contract instance and then pair it with an IbPy instance, 
        which will be sent to the IB API. This method, create_contract, 
        generates the first component of this pair. It expects a ticker
        symbol, a security type (e.g. stock or future), an exchange/primary
        exchange, and a currency.

        Parameters
        ----------
        symbol : 'str'
            The ticker symbol for the contract.
        sec_type : 'str'
            The security type for the contract ('STK' is 'stock').
        exch : 'str'
            The exchange to carry out the contract on.
        prim_exch : 'str'
            The primery exchange to carry out the contract on.
        curr : 'str'
            The currency in which to produce the contract.

        Returns
        -------
        'Contract'
            Returns an IbPy Contract instance.

        """
        
        contract = Contract()
        contract.m_symbol = symbol
        contract.m_secType = sec_type
        contract.m_exchange = exch
        contract.m_primaryExch = prim_exch
        contract.m_currency = curr
        return contract
    
    
    def create_order(self, order_type, quantity, action):
        """
        Create an Order object (Market/Limit) to go Long/Short.
        
        This methos creates that second component of the pair, namely
        the Order instance. 

        Parameters
        ----------
        order_type : 'str'
            'MKT', 'LMT' for Market or Limit orders.
        quantity : 'int'
            Integral number of assets to order.
        action : 'str'
            'BUY' or 'SELL'.

        Returns
        -------
        'Order'
            Returns an IbPy Order instance.

        """
        
        order = Order()
        order.m_orderType = order_type
        order.m_totalQuantity = quantity
        order.m_action = action
        return order
    
    
    def create_fill_dict_entry(self, msg):
        """
        Creates an entry in the Fill Dictionary that lists orderIds
        and provides security information. This is needed for the 
        event-driven behaviour of the IB server message behaviour.
        
        When a fill has been generated, the "filled" key of an entry
        for a particular order ID is set to True. If a subsequent
        "Server Response" message is received from IB stating that an
        order has been filled (and is a duplicate message), it will not
        lead to a new fill.


        Returns
        -------
        None.

        """
        
        self.fill_dict[msg.orderId] = {
            "symbol": msg.contract.m_symbol,
            "exchange": msg.contract.m_exchange,
            "direction": msg.order.m_action, 
            "filled": False
        }
        
    
    def create_fill(self, msg):
        """
        Handles the creationg of the FillEvent that will be placed
        onto the events queue subsequent to an order being filled.
        
        This methos is the one that actually created the FillEvent.


        Returns
        -------
        None.

        """
        
        fd = self.fill_dict[msg.orderId]
        
        # Prepare the fill data
        symbol = fd["Symbol"]
        exchange = fd["exchange"]
        filled = msg.filled
        direction = fd["direction"]
        fill_cost = msg.avgFillPrice
        
        # Create a FillEvent object
        fill = FillEvent(
            datetime.datetime.utcnow(), symbol, 
            exchange, filled, direction, fill_cost
        )
        
        # Make sure that multiple messages don't create 
        # additional fills.
        self.fill_dict[msg.orderId]["filled"] = True
        
        # Place the fill event onto the event queue
        self.events.put(fill_event)
        
        
    def execute_order(self, event):
        """
        Creates the necessary InteractiveBrokers order object
        and submits it to IB via their API.
        
        The results are then queried in order to generate a 
        corresponding Fill object, which is placed back on the 
        event queue.
        
        This is the method that actually carries out the order 
        placement with the IB API.
        
        We first check that the event being received to this method
        is actually an OrderEvent and then prepare the Contract and
        Order objects with their respective parameters. Once both are
        created the IbPy method placeOrder of the connection object is
        called with an associated order_id.
        
        It is EXTREMELY important to call the time.sleep(1) method
        to ensure that the order actually goes through to IB.

        Parameters
        ----------
        event : 'Event'
            The Event object with order information.

        Returns
        -------
        None.

        """
        
        if event.type == 'ORDER':
            # Prepare the parameters for the asset order
            asset = event.symbol
            asset_type = "STK"
            order_type = event.order_type
            quantity = event.quantity
            direction = event.direction
            
            
            # Create the Interactive Brokers contract via
            # the passed OrderEvent
            ib_contract = self.create_contract(
                asset, asset_type, self.order_routing,
                self.order_routing, self.currency
            )
        
            # Create the Interactive Broker order via 
            # the passed OrderEvent
            ib_order = self.create_order(order_type, quantity, direction)
            
            # Use the connection to send the order to IB
            self.tws_conn.placeOrder(
                self.order_id, ib_contract, ib_order
            )
            
            # NOTE: This following line is crucial
            # It ensures the order goes through
            time.sleep(1)
            
            # Increment the order ID for this session
            self.order_id += 1
        