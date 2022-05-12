from asyncio.log import logger
from multiprocessing.sharedctypes import Value
from optparse import Values
from urllib.request import HTTPBasicAuthHandler
import streamlit as st
from logging import getLogger
import numpy as np
import pandas as pd
# from polygon import RESTClient
import datetime as dt
import requests
import json

loggers =  getLogger()

ALPACA_API_KEY = 'tpHEpdlolUR703YTAdrvOHaUMW6PEDPw' #os.environ.get('ALPACA_API_KEY')
# URL for all the tickers on Polygon
# POLYGON_TICKERS_URL = 'https://api.polygon.io/v2/reference/tickers?page={}&apiKey={}'
POLYGON_TICKERS_URL = 'https://api.polygon.io/v3/reference/tickers?active={}&sort=ticker&order={}&limit={}'
# URL FOR PRICING DATA - Note, getting pricing that is UNADJUSTED for splits, I will try and adjust those manually
POLYGON_AGGS_URL = 'https://api.polygon.io/v2/aggs/ticker/{}/range/{}/{}/{}/{}'
# URL FOR DIVIDEND DATA
POLYGON_DIV_URL = 'https://api.polygon.io/v2/reference/dividends/{}?apiKey={}'
# URL FOR STOCK SPLITS
POLYGON_SPLIT_URL = 'https://api.polygon.io/v2/reference/splits/{}?apiKey={}'
#URL FOR TICKER TYPES
POLYGON_TYPES_URL = 'https://api.polygon.io/v2/reference/types?apiKey={}'

class polygon_api:
    '''Authorization: Bearer tpHEpdlolUR703YTAdrvOHaUMW6PEDPw
    'https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2020-06-01/2020-06-17?apiKey=tpHEpdlolUR703YTAdrvOHaUMW6PEDPw'
    demo url = 'https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2021-07-22/2021-07-22?adjusted=true&sort=asc&limit=120&apiKey=tpHEpdlolUR703YTAdrvOHaUMW6PEDPw
    token is unique token for authorization 
    url is base url of the the api'''


    def __init__(self) :
        self.token = 'tpHEpdlolUR703YTAdrvOHaUMW6PEDPw'
        self.authorization = {'Authorization':'Bearer '+ self.token}
        # self.url = 'https://api.polygon.io/v2/'

    def get_tickers(self,active=True,order='asc',limit=1000):
        '''this method is use to get list of tickers
        return : 
        list of tickers '''
        try:
            logger.error(f'get ticker : Try block called')

            ticker_url = POLYGON_TICKERS_URL.format(active,order,limit)
            ticker_json = self.get_data(ticker_url)
            # print(ticker_json)
            ticker_df = pd.DataFrame(ticker_json['results'])
            # ticker_df.to_csv('data/tickers/tickerlist.csv', index=False)
            return ticker_df
        except Exception as e:
            logger.error(f'get ticker : exception block called {e}')


    def get_aggregate(self,stocksTicker,multiplier,timespan,from_date,to_date):
        ''' Request : 
            Stock Ticker : str :  Name of Stock
            Multiplier : int : Count of timespan
            timespan : string :day / hours / minute  
            Multiplier is 5 and timespan is minute then 5-minute bar will return.
            from_date : datetime as str : from date 
            to_date : datetime as str : to date 
            Method: get
            request url : /v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to} 
            Response : Data Frame of the particular stock'''    
        try:
            logger.info('Start get_aggregate : try block method')
            method_url = (POLYGON_AGGS_URL.format(stocksTicker,multiplier,timespan,from_date,to_date)) # f'aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from_date}/{to_date}'
            
            logger.info('Get method call: try block method')
            response_json = self.get_data(method_url)
            logger.info(f'Get method called: try block method \n {response_json}')
            # aggreget_response_df = pd.DataFrame(response_json)
            if response_json['status']  != 'ERROR':
                if response_json['queryCount'] > 0:
                    logger.info('get_aggregate : If block Call')
                    # print(response_json)
                    stock_name = response_json['ticker']
                    stock_result = response_json['results']

                    aggreget_response_df = pd.DataFrame(stock_result)
                    aggreget_response_df = aggreget_response_df.rename({'v':'volume','vw':'volume_weight','o':'open','c':'close','h':'high','l':'low','t':'date','n':'no_of_trans'}, axis=1)  # new method
                    # logger.info(f'convert to df :   {aggreget_response_df}')
                    # aggreget_response_df['t'] = pd.to_datetime(aggreget_response_df['t'], format='%Y%m%d')
                    aggreget_response_df.date = aggreget_response_df["date"].apply(self.get_date)

                    aggreget_response_df.sort_values(by=['date'], inplace=True)
                    stock_details = (stock_name,aggreget_response_df)
                    # aggreget_response_df.to_csv(f'data/stockdetails/{stock_name}.csv')
                    return stock_details
                else:
                    logger.info('get_aggregate : Else block Call')
                    stock_details = (f'No Data Found For  {stocksTicker}',[])
                    return stock_details
            else:
                stock_details = (f'No Data Found For  {stocksTicker}',[])
                return stock_details
        except Exception as e:
            logger.error(f'get_aggregate : Except block Call {e}')

    def get_data(self,method_url):
        '''THIS METHOD IS USE FOR THE CALL THE GET API TO polygon.io 
        Request :
        method url: url of the method with get request  
        Response : 
        json text 
        ticker : stock name
        result : stock detail
            'o' : The open price for the symbol in the given time period
            'c' : The highest price for the symbol in the given time period.
            'h' : The highest price for the symbol in the given time period.
            'l' : The open price for the symbol in the given time period
            'v' : The trading volume of the symbol in the given time period.
            'vw' : The volume weighted average price
            't' : The Unix Msec timestamp for the start of the aggregate window.
            'n' : The open price for the symbol in the given time period '''
        try:
            logger.info('get_data : try block')
            # api_url = self.url + method_url

            logger.info(f' get request url : {method_url}')
            response = requests.get(method_url,  headers=self.authorization)
            agg_content = json.loads(response.text)
            return agg_content
        except Exception as e:
            logger.error(f'get_data : except Block {e}')
            raise e
    
    def get_date(self, created):
        '''this method is convert timestamp to data time formate''' 
        try:
            # logger.info(f'get_date : try block call {created}')
            return dt.datetime.fromtimestamp((created/1000))
        except Exception as e:
            logger.info(f'get_date : exception block call { e} ')


aggreget_api = polygon_api()

# Get List of Ticker
# ticker_list = aggreget_api.get_tickers()
ticker_list = pd.read_csv("data/tickers/tickerlist.csv")
# Display List of Ticker
st.subheader(f'Ticker List')
st.write(ticker_list)

# get list of ticker and name
ticker_dd = ticker_list[['name','ticker']]
# Combain Name and ticker
combine_ticker_name = ticker_dd['ticker'].str.cat(ticker_dd[['name']], sep='-')
# get the index of AAPL ticker or default load
default_ix = combine_ticker_name.tolist().index('AAPL-Apple Inc.')
stock_details = []

todays_date = dt.datetime.now().date() 

def getTickerdetails(ticker_name):
    if(ticker_name):
        logger.info('getTickerdetails : if Condition BEFOR SPLIT called tikker Name {}'.format(ticker_name))
        ticker_value = ticker_name.split('-')
        ticker_name = ticker_value[0]

        # getTickerdetails(ticker_value[0])
        logger.info('getTickerdetails : if Condition called tikker Name {}'.format(ticker_name))
        stock_details = aggreget_api.get_aggregate(ticker_name.upper(),1,'day','2021-01-01',todays_date)

        if len(stock_details[1]) > 0:
            # display the details of stock 
            st.subheader(f'{stock_details[0]} Stock Data')
            st.write(stock_details[1])

            # line chart
            st.subheader(f'{stock_details[0]}stock price Open data')
            st.line_chart(stock_details[1].open)
        else:
            st.warning(f' {stock_details[0]}')
    else:
        logger.info('getTickerdetails : else Condition called tikker Name {}'.format(ticker_name))
        st.warning('Please Enter Tickker Name')

col1,col2,col3 = st.columns([1,1,1])
with col1:
    # Create Select box
    ticker_name = st.selectbox('Select Ticker :',combine_ticker_name,index = default_ix)
with col2:
    ticker_txt_Name = st.text_input('Enter Ticker:',key='txt_ticker_name')

if ticker_txt_Name:
    ticker_name = ticker_txt_Name
if st.button('Search'):
     getTickerdetails(ticker_name)
# st.button('Submit',on_click=getTickerdetails(ticker_name),key='btn_ticker_submit')

# # Check if Ticker name is selected or not
# if ticker_name :
#     # split ticker and name for get ticker
#     ticker_value = ticker_name.split('-')

#     getTickerdetails(ticker_value[0])
    # Call the aggregate method for get the detail of stock 
    # stock_details = aggreget_api.get_aggregate(ticker_value[0],1,'day','2021-01-01',todays_date)

# # display the details of stock 
# st.subheader(f'{stock_details[0]} Stock Data')
# st.write(stock_details[1])

# # line chart
# st.subheader(f'{stock_details[0]}stock price Open data')
# st.line_chart(stock_details[1].open)

