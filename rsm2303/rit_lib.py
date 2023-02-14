import requests
import time
import math

#######################################
########## common variables ###########
#######################################
rit_status_map = {
    'ACTIVE': 1,
    'STOPPED': 0,
    'PAUSED': -1
}

helper = {
    'cases':['atv1','lt3'],
    'atv1': {
        'name': 'Agency Trading 1v Case',
        'param': ['strategy','strategy_param'],
        'default_param': ['vwap',1],
        'explain': 'strategy: vwap, twap; \nstrategy_param defines trading frequency in each trading window'
    }
}

#######################################
#######################################
#######################################

class rit:
    def __init__(self,refresh_rate=0.25,mode='auto'):
        self.url = 'http://localhost:9999/v1'
        self.headers = {
            'accept':'application/json',
            'X-API-Key':'2Z1G4ZT0'
        }
        self.refresh_rate = refresh_rate
        self.prep = self.prepare_algo()
        if self.prep != 0:
            self.case_name = self.prep[0]
            self.rit_status = self.prep[1]
            self.limits = self.prep[2]
            if mode == 'auto':
                self.wait_for_new_iteration()
                if self.case_name == 'Agency Trading 1v Case':
                    self.at1v()
                elif self.case_name == 'Liability Trading 3 Case':
                    self.lt3()
            elif mode == 'debug':
                print('algo warned up, trigger case methods manually')



    


    #######################################
    ##### code endpoints as functions #####
    #######################################

    def get_case(self):
        return requests.get(f'{self.url}/case',headers=self.headers)
    
    def get_trading_limits(self):
        return requests.get(f'{self.url}/limits',headers=self.headers)
    
    def get_news(self,news_id=0,limit=100):
        payload = {
            'since':news_id,
            'limit':limit
        }
        return requests.get(f'{self.url}/news',params=payload,headers=self.headers)
    
    def get_securities(self,*args):
        if len(args) == 0:
            return requests.get(f'{self.url}/securities',headers=self.headers)
        else:
            payload = {
                'ticker':args[0]
            }
            return requests.get(f'{self.url}/securities',headers=self.headers,params=payload)

    def insert_order(self,ticker,quantity,order_type,action,*args):
        
        limit = [i['trade_limit'] for i in self.limits if i['ticker'] == ticker][0] - 1
        number_of_orders = math.ceil(quantity/limit)
        print(f"{number_of_orders} in total will be sent to RIT...")
        if action == 'BUY':
            res = {
                'ticker': ticker,
                'action': 'BUY',
                'quantity': 0,
                'vwap': 0
            }
        else:
            res = {
                'ticker': ticker,
                'action': 'SELL',
                'quantity': 0,
                'vwap': 0
            }
        order_count = 1
        while order_count < number_of_orders:
            if len(args) == 0:
                payload = {
                    'ticker': ticker,
                    'type': order_type,
                    'quantity': limit,
                    'action': action,
                }
            else:
                payload = {
                    'ticker': ticker,
                    'type': order_type,
                    'quantity': limit,
                    'action': action,
                    'price': args[0]
                }
            order_req = requests.post(f"{self.url}/orders",headers=self.headers,params = payload)
            print(f"Order #{order_count} is sent, quantity = {payload['quantity']}!")
            print(f"Order #{order_count} status: {order_req.status_code}; RIT confirmation message: {order_req.json()}")
            order = order_req.json()
            res['quantity_filled'] += order['quantity_filled']
            res['vwap'] = (res['vwap'] * res['quantity_filled'] + order['price'] * order['quantity_filled'])/(res['quantity'] + order['quantity_filled'])
            order_count += 1
        if len(args) == 0:
            payload = {
                'ticker': ticker,
                'type': order_type,
                'quantity': quantity - limit*(order_count-1),
                'action': action,
            }
        else:
            payload = {
                'ticker': ticker,
                'type': order_type,
                'quantity': quantity - limit*(order_count-1),
                'action': action,
                'price': args[0]
            } 
        order_req = requests.post(f"{self.url}/orders",headers=self.headers,params = payload)
        print(f"Order #{order_count} is sent, quantity = {payload['quantity']}!")
        print(f"Order #{order_count} status: {order_req.status_code}; RIT confirmation message: {order_req.json()}")
        res['quantity_filled'] += order['quantity_filled']
        res['vwap'] = (res['vwap'] * res['quantity_filled'] + order['price'] * order['quantity_filled'])/(res['quantity'] + order['quantity_filled'])
        return res
    
    def get_tender(self):
        return requests.get(f"{self.url}/tenders",headers=self.headers)
    
    def get_order_book(self,ticker):
        payload = {
            'ticker':ticker
        }
        return requests.get(f"{self.url}/securities/book",headers=self.headers,params=payload)

    def execute_tender(self,tender_id,action):
        if action == True:
            return requests.post(f"{self.url}/tenders/{tender_id}",headers=self.headers)
        else:
            return requests.delete(f"{self.url}/tenders/{tender_id}",headers=self.headers)
    ######################################t#
    #######################################
    #######################################

    #######################################
    ########## helper functions ###########
    #######################################
    def helper(self,*args):
        if len(args) == 0:
            print(f"Input a case to check detail: {helper['cases']}.")
        else:
            print(f"{helper[args[0]]}")
    
    def wait(self,seconds):
        time.sleep(seconds)

    ##check connection and query case info
    def prepare_algo(self):
        print("Algo Initiated")
        case_res = self.get_case()
        if case_res.status_code != 200:
            print(f"RIT API connection issue: {case_res.status_code}")
            return 0
        else:
            name = case_res.json()['name']
            status = rit_status_map[case_res.json()['status']]
            limits_res = self.get_trading_limits()
            securities_res = self.get_securities()
            trading_limits = limits_res.json()[0]['net_limit']
            securities = securities_res.json()
            ## check trading limit for each security and override if limit overseeds overall trading limit
            for security in securities:
                if security['max_trade_size'] > trading_limits:
                    security['max_trade_size'] = trading_limits
            security_limits = [
                {
                    'ticker':security['ticker'],
                    'trade_limit':security['max_trade_size']
                }
                for security in securities
            ]
            print(f"RIT API connection health check successful, Algo set to: {name}!")
            print(f"{','.join([security['ticker'] for security in security_limits])} available for this case.")
            return [name,status,security_limits]
            
    ##This is a blocker function that prevent the actual code from initiating until a new iteration starts
    def wait_for_new_iteration(self):
        ## if an iteration is running, wait for it to finish
        while self.rit_status != 0:
            case_res = self.get_case()
            self.rit_status = rit_status_map[case_res.json()['status']]
            print(f"Await completion of current iteration, {case_res.json()['ticks_per_period'] - case_res.json()['tick']} seconds remaining")
            self.wait(self.refresh_rate)
        
        ## if an rit is stopped, wait for it to start a new iteration
        while self.rit_status != 1:
            print(f"Await new iteration")
            self.wait(self.refresh_rate)
            self.rit_status = rit_status_map[self.get_case().json()['status']]
        
        print(f"New iteration starts... \nLet's Rock !!!")
        
    #######################################
    #######################################
    #######################################

    #######################################
    ########### case functions ############
    #######################################

    def at1v(self,params=['vwap',1]):
        available_strategies = ['twap','vwap','vtwap']
        self.result = []
        if params[0] not in available_strategies:
            print(f'Please enter valid strategy name: {available_strategies}')
        else:
            if params[0] == 'twap':
                #define some params
                order_size = round(100000/params[1],0)
                order_frequency = params[1]
                wait_time = 300/order_frequency
                last_order_size = 100000 - (order_frequency-1) * order_size
                ## define per order in a list
                orders = []
                counter = 1
                while counter < order_frequency:
                    orders.append(order_size)
                    counter += 1
                orders.append(last_order_size)
            elif params[0] == 'vwap':
                new_length = 1
                while new_length != 2:
                    news_req = self.get_news()
                    new_length = len(news_req.json())
                news = news_req.json()
                print(news)
                vols = list(map(lambda x: int(x), news[0]['body'].split(";")[1:]))    
                print(self.get_news().status_code,self.get_news().json())
                print(self.get_news().json()[0]['body'])
                print(vols)
                vol = sum(vols)
                order_size = list(map(lambda x: round(x*100000/vol,0),vols))
                last_order_size = 100000 - sum(order_size[:-1])
                order_size[-1] = last_order_size
                order_frequency = params[1]
                wait_time = 300/39/order_frequency
                orders = []
                for i in range(0,len(order_size)):
                    if i < len(order_size)-1:
                        for j in range(0,order_frequency):
                            if j < order_frequency-1:
                                orders.append(round(order_size[i]/order_frequency,0))
                            else:
                                orders.append(order_size[i] - round(order_size[i]/order_frequency,0)*j)
                    else:
                        orders.append(order_size[i])
                print(orders)
        
        #insert orders
        for i in orders:
            order_res = self.insert_order(self.limits[0]['ticker'],"MARKET",i,"BUY")
            order_res_data = order_res.json()
            self.result.append(
                {
                    'order_id':order_res_data['order_id'],
                    'quantity_filled':order_res_data['quantity_filled'],
                    'price':order_res_data['price'],
                    'tick':order_res_data['tick']
                }
            )
            time.sleep(wait_time)

    def lt3(self,safe_margin = 0,price_epsilon = 0.01):
        while self.rit_status == 1:
            case_res = self.get_case()
            case = case_res.json()

            tenders_res = self.get_tender()
            tenders = tenders_res.json()
            if len(tenders) > 0:
                print(f"Tender order detected!")
                for tender in tenders:
                    tender_id = tender['tender_id']
                    tender_action = tender['action']
                    tender_ticker = tender['ticker']
                    tender_quantiy = tender['quantity']
                    tender_price = tender['price']
                    print(f"Tender Order: {tender_id}, {tender_action},{tender_ticker},{tender_price},{tender_quantiy}")
                    order_book_res = self.get_order_book(tender_ticker)
                    order_book = order_book_res.json()
                    if tender_action == "BUY":
                        live_orders = [order for order in order_book['bids'] if order['status'] == 'OPEN']
                        remaining_fill = tender_quantiy
                        for order in live_orders:
                            if  remaining_fill >= order['quantity'] - order['quantity_filled']:
                                order['pl'] = (order['quantity'] - order['quantity_filled']) * (order['price'] - tender_price)
                                remaining_fill = remaining_fill - (order['quantity'] - order['quantity_filled'])
                                order['potential_fill_quantity'] = order['quantity'] - order['quantity_filled']
                            else:
                                order['pl'] = remaining_fill * (order['price'] - tender_price)
                                order['potential_fill_quantity'] = remaining_fill
                                remaining_fill = 0
                        print(f"safe marge: {sum([order['pl'] for order in live_orders])}")
                        print(f"{live_orders}")
                        if sum([order['pl'] for order in live_orders]) > safe_margin:
                            execute_tender_status = 0
                            while execute_tender_status != 200:
                                execute_tender_req = self.execute_tender(tender_id,True)
                                execute_tender_status = execute_tender_req.status_code
                                self.wait(0.1)
                            print(f"Accept tender offer")
                            print(f"Tender Offer execution status: {execute_tender_status}; RIT confirmation message: {execute_tender_req.json()}")
                            tender_register_status = tender_quantiy
                            while tender_register_status != 0:
                                position_res = self.get_securities(tender_ticker)
                                position = position_res.json()[0]['position']
                                tender_register_status = tender_quantiy - position
                                self.wait(0.05)
                            for order in live_orders:
                                if order['potential_fill_quantity'] > 0:
                                    self.insert_order(tender_ticker,order['potential_fill_quantity'],"LIMIT","SELL",order['price']-price_epsilon)
                            os_position_res = self.get_securities(tender_ticker)
                            os_position = os_position_res.json()[0]['position']
                            print(f'Outstanding Position: {os_position}')
                            if os_position > 0:
                                self.insert_order(tender_ticker,os_position,'MARKET','SELL')
                            elif os_position < 0:
                                self.insert_order(tender_ticker,os_position*-1,'MARKET','BUY')
                            else:
                                print('All positions from tender order is filled')
                        else: 
                            execute_tender_status = 0
                            while execute_tender_status != 200:
                                execute_tender_req = self.execute_tender(tender_id,False)
                                execute_tender_status = execute_tender_req.status_code
                            print(f"Reject tender offer")
                            print(f"Tender Offer execution status: {execute_tender_status}; RIT confirmation message: {execute_tender_req.json()}")
                    elif tender_action == "SELL":
                        live_orders = [order for order in order_book['asks'] if order['status'] == 'OPEN']
                        remaining_fill = tender_quantiy
                        for order in live_orders:
                            if  remaining_fill >= order['quantity'] - order['quantity_filled']:
                                order['pl'] = (order['quantity'] - order['quantity_filled']) * (order['price'] - tender_price) * -1
                                remaining_fill = remaining_fill - (order['quantity'] - order['quantity_filled'])
                                order['potential_fill_quantity'] = order['quantity'] - order['quantity_filled']
                            else:
                                order['pl'] = remaining_fill * (order['price'] - tender_price) * -1
                                order['potential_fill_quantity'] = remaining_fill
                                remaining_fill = 0
                        print(f"safe marge: {sum([order['pl'] for order in live_orders])}")
                        print(f"{live_orders}")
                        if sum([order['pl'] for order in live_orders]) > safe_margin:
                            execute_tender_status = 0
                            while execute_tender_status != 200:
                                execute_tender_req = self.execute_tender(tender_id,True)
                                execute_tender_status = execute_tender_req.status_code
                                self.wait(0.1)
                            print(f"Tender Offer execution status: {execute_tender_status}; RIT confirmation message: {execute_tender_req.json()}")
                            tender_register_status = tender_quantiy
                            while tender_register_status != 0:
                                position_res = self.get_securities(tender_ticker)
                                position = position_res.json()[0]['position']
                                tender_register_status = tender_quantiy + position
                                self.wait(0.05)
                            for order in live_orders:
                                if order['potential_fill_quantity'] > 0:
                                    self.insert_order(tender_ticker,order['potential_fill_quantity'],"LIMIT","BUY",order['price']+price_epsilon)
                            os_position_res = self.get_securities(tender_ticker)
                            os_position = os_position_res.json()[0]['position']
                            print(f'Outstanding Position: {os_position}')
                            if os_position > 0:
                                self.insert_order(tender_ticker,os_position,'MARKET','SELL')
                            elif os_position < 0:
                                self.insert_order(tender_ticker,os_position*-1,'MARKET','BUY')
                            else:
                                print('All positions from tender order is filled')
                        else: 
                            execute_tender_status = 0
                            while execute_tender_status != 200:
                                execute_tender_req = self.execute_tender(tender_id,False)
                                execute_tender_status = execute_tender_req.status_code
                            print(f"Reject tender offer")
                            print(f"Tender Offer execution status: {execute_tender_status}; RIT confirmation message: {execute_tender_req.json()}")
            
            else:
                print(f"No tender order, {case['ticks_per_period']-case['tick']} seconds remaining")

            self.wait(self.refresh_rate)
            self.rit_status = rit_status_map[case['status']]
                            
                                

    #######################################
    #######################################
    #######################################