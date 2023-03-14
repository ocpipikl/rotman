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
                elif self.case_name == 'Algorithmic Trading 3':
                    self.algo3()
                elif self.case_name == 'Value-at-Risk Case':
                    self.var()
            elif mode == 'debug':
                print('Debug mode on... \nalgo warned up... \ntrigger case methods manually...')



    


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
        res = []
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
            order = order_req.json()
            print(f"Order #{order_count} is sent, quantity = {payload['quantity']}!")
            print(f"Order #{order_count} status: {order_req.status_code}; RIT confirmation message: {order}")
            res.append(order)
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
        order = order_req.json()
        print(f"Order #{order_count} is sent!")
        print(f"Order #{order_count} status: {order_req.status_code}; RIT confirmation message: {order}")
        res.append(order)
        return res

    def get_orders(self,status='OPEN'):
        payload = {
            'status':status
        }
        return requests.get(f"{self.url}/orders",headers=self.headers,params=payload)
    
    def delete_order(self,order_id):
        return requests.delete(f"{self.url}/orders/{order_id}",headers=self.headers)
    
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

    def calc_var(self,w1,w2,w3,e1,e2,e3,sig1,sig2,sig3,rho12,rho13,rho23):
        er = w1*e1+w2*e2+w3*e3
        variance = (w1**2)*(sig1**2)+(w2**2)*(sig2**2)+(w3**2)*(sig3**2)+(2*w1*w2)*(sig1*sig2)*rho12+(2*w1*w3)*(sig1*sig3)*rho13+(2*w2*w3)*(sig2*sig3)*rho23
        sig = variance**0.5
        z = -2.32634787404084
        return er+z*sig
    
    def get_nbbo(self,ticker_m,ticker_a,type):
        order_book_m = self.get_order_book(ticker_m).json()
        order_book_a = self.get_order_book(ticker_a).json()

        if type == "asks":
            live_orders_m = order_book_m['asks']
            live_orders_a = order_book_a['asks']

            nbbo_raw = []
            nbbo_raw.extend(live_orders_m)
            nbbo_raw.extend(live_orders_a)

            nbbo = sorted(nbbo_raw,key=lambda d:d['price'])

        elif type == "bids":
            live_orders_m = order_book_m['asks']
            live_orders_a = order_book_a['asks']

            nbbo_raw = []
            nbbo_raw.extend(live_orders_m)
            nbbo_raw.extend(live_orders_a)

            nbbo = sorted(nbbo_raw,key=lambda d:d['price'],reverse=True)

        return nbbo


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
            if (case_res.json()['ticks_per_period'] - case_res.json()['tick']) / 10 == (case_res.json()['ticks_per_period'] - case_res.json()['tick']) // 10:
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

    def lt3(self,safety_margin = 1000,price_epsilon = 0.02):
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
                    tender_register_tic = time.perf_counter()
                    order_book_res = self.get_order_book(tender_ticker)
                    order_book = order_book_res.json()
                    if tender_action == "BUY":
                        live_orders = [order for order in order_book['bids'] if order['status'] == 'OPEN']
                        remaining_fill = tender_quantiy
                        for order in live_orders:
                            if  remaining_fill >= order['quantity'] - order['quantity_filled']:
                                order['pl'] = (order['quantity'] - order['quantity_filled']) * (order['price'] - tender_price)
                                remaining_fill = remaining_fill - (order['quantity'] - order['quantity_filled'])
                            else:
                                order['pl'] = remaining_fill * (order['price'] - tender_price)
                                remaining_fill = 0
                        print(f"safe margin: {sum([order['pl'] for order in live_orders])}")
                        # print(f"{live_orders}") ##this line to show calculated safe margin vs order book for debugging
                        if sum([order['pl'] for order in live_orders]) > safety_margin:
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
                            tender_register_toc = time.perf_counter()
                            print(f"Tender registered in {tender_register_toc - tender_register_tic:0.6f}s...")
                            os_position = tender_quantiy
                            order_book_res = self.get_order_book(tender_ticker)
                            order_book = order_book_res.json()['bids']
                            # print(f'order book 2:{order_book}') ##Line for debugging
                            ##run down the order book from the top
                            print(f"recall order book takes: {tender_register_toc-time.perf_counter():0.6f}s")
                            limit_order_tic = time.perf_counter()
                            for order in order_book:
                                print('next order book',os_position,order['quantity'] - order['quantity_filled'])
                                if (os_position > 0) & (os_position>=(order['quantity'] - order['quantity_filled'])) & (order['quantity'] - order['quantity_filled'] > 0):
                                    # print('sell logic 1') ##Line for debugging
                                    order_req = self.insert_order(tender_ticker,(order['quantity']-order['quantity_filled']),"LIMIT","SELL",tender_price+price_epsilon)
                                    os_position -= order['quantity']-order['quantity_filled']
                                    print(f"{os_position} remaining to fill")
                                elif (os_position > 0) & (os_position<(order['quantity'] - order['quantity_filled'])) & (order['quantity'] - order['quantity_filled'] > 0):
                                    # print('sell logic 2') ##Line for debugging
                                    order_req = self.insert_order(tender_ticker,os_position,"LIMIT","SELL",tender_price+price_epsilon)
                                    os_position = 0
                                    print(f"{os_position} remaining to fill")
                            print(f"All limit orders submitted in {time.perf_counter()-limit_order_tic:0.6f}s") #this is a timer for testing
                            ##check os position after complete the order book and fill the rest with MARKET
                            wait_time = 0
                            open_orders_count = 1
                            while (wait_time < 8) & (open_orders_count != 0):
                                self.wait(0.25)
                                open_orders_res = self.get_orders()
                                open_orders = open_orders_res.json()
                                open_orders_count = len(open_orders)
                                limit_order_toc = time.perf_counter()
                                print(f"check open orders: {wait_time+1}, {open_orders_count}")
                                wait_time += 1

                            if open_orders_count != 0:
                                print('There are still unfilled limit orders; These orders will be cancelled now')
                                for open_order in open_orders:
                                    del_req = self.delete_order(open_order['order_id'])
                                    print(f"Delete order {open_order['order_id']}; Status: {del_req.status_code}")
                                    os_position += open_order['quantity'] - open_order['quantity_filled']
                            else:
                                print(f"All limit orders are filled in {limit_order_toc-limit_order_tic:0.6f}s!!!")
                            
                            os_position_res = self.get_securities(tender_ticker)
                            os_position = os_position_res.json()[0]['position']
                            if os_position != 0:
                                print(f"All order book cleared, {os_position} remaining, fill with market order")
                                self.insert_order(tender_ticker,os_position,"MARKET","SELL")
                            else:
                                print(f"tender order cleared with limit orders")
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
                            else:
                                order['pl'] = remaining_fill * (order['price'] - tender_price) * -1
                                remaining_fill = 0
                        print(f"safe margin: {sum([order['pl'] for order in live_orders])}")
                        # print(f"{live_orders}") ##This line is for debugging
                        if sum([order['pl'] for order in live_orders]) > safety_margin:
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
                            tender_register_toc = time.perf_counter()
                            print(f"Tender registered in {tender_register_toc - tender_register_tic:0.6f}s...")
                            os_position = tender_quantiy
                            order_book_res = self.get_order_book(tender_ticker)
                            order_book = order_book_res.json()['asks']
                            # print(f'order book 2:{order_book}') ##Line for debugging
                            ##run down the order book
                            print(f"recall order book takes: {tender_register_toc-time.perf_counter():0.6f}s")
                            limit_order_tic = time.perf_counter()
                            for order in order_book:
                                print('next order book',os_position,order['quantity'] - order['quantity_filled'])
                                if (os_position > 0) & (os_position>=(order['quantity'] - order['quantity_filled'])) & (order['quantity'] - order['quantity_filled'] > 0):
                                    # print('buy logic 1') ##Line for debugging
                                    order_req = self.insert_order(tender_ticker,(order['quantity']-order['quantity_filled']),"LIMIT","BUY",tender_price-price_epsilon)
                                    os_position -= order['quantity']-order['quantity_filled']
                                    print(f"{os_position} remaining to fill")
                                elif (os_position > 0) & (os_position<(order['quantity'] - order['quantity_filled'])) & (order['quantity'] - order['quantity_filled'] > 0):
                                    # print('buy logic 2') ##Line for debugging
                                    order_req = self.insert_order(tender_ticker,os_position,"LIMIT","BUY",tender_price-price_epsilon)
                                    os_position = 0
                                    print(f"{os_position} remaining to fill")
                            print(f"All limit orders submitted in {time.perf_counter()-limit_order_tic:0.6f}s") #this is a timer for testing
                            ##check os position after complete the order book and fill the rest with MARKET
                            wait_time = 0
                            open_orders_count = 1
                            while (wait_time < 8) & (open_orders_count != 0):
                                self.wait(0.25)
                                open_orders_res = self.get_orders()
                                open_orders = open_orders_res.json()
                                open_orders_count = len(open_orders)
                                limit_order_toc = time.perf_counter()
                                print(f"check open orders: {wait_time+1}, {open_orders_count}")
                                wait_time += 1

                            if open_orders_count != 0:
                                print('There are still unfilled limit orders; These orders will be cancelled now')
                                for open_order in open_orders:
                                    del_req = self.delete_order(open_order['order_id'])
                                    print(f"Delete order {open_order['order_id']}; Status: {del_req.status_code}")
                            else:
                                print(f"All limit orders are filled in {limit_order_toc-limit_order_tic:0.6f}s!!!")

                            os_position_res = self.get_securities(tender_ticker)
                            os_position = os_position_res.json()[0]['position']
                            if os_position != 0:
                                print(f"All order book cleared, {os_position} remaining, fill with market order")
                                self.insert_order(tender_ticker,os_position*-1,"MARKET","BUY")
                            else:
                                print(f"tender order cleared with limit orders")
                                
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
                            
    def algo3(self,safety_margin = 500, price_epsilon = 0.02):
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
                    tender_register_tic = time.perf_counter()
                    if tender_action == "BUY":
                        live_orders = self.get_nbbo("THOR_M","THOR_A","bids")
                        remaining_fill = tender_quantiy
                        profitable_volume = 0
                        profit = 0
                        for order in live_orders:
                            if  remaining_fill >= order['quantity'] - order['quantity_filled']:
                                profit += (order['quantity'] - order['quantity_filled']) * (order['price'] - tender_price)
                                remaining_fill = remaining_fill - (order['quantity'] - order['quantity_filled'])
                            else:
                                profit += remaining_fill * (order['price'] - tender_price)
                                remaining_fill = 0
                                break
                        print(f"safety margin: {profit}")
                        print(f"safety volume: {profitable_volume}")
                        # print(f"{live_orders}") ##this line to show calculated safe margin vs order book for debugging
                        if profit > safety_margin:
                            execute_tender_status = 0
                            while execute_tender_status != 200:
                                execute_tender_req = self.execute_tender(tender_id,True)
                                execute_tender_status = execute_tender_req.status_code
                                self.wait(0.05)
                            print(f"Accept tender offer")
                            print(f"Tender Offer execution status: {execute_tender_status}; RIT confirmation message: {execute_tender_req.json()}")
                            tender_register_status = tender_quantiy
                            while tender_register_status != 0:
                                position_res = self.get_securities(tender_ticker)
                                position = position_res.json()[0]['position']
                                tender_register_status = tender_quantiy - position
                                self.wait(0.05)
                            tender_register_toc = time.perf_counter()
                            print(f"Tender registered in {tender_register_toc - tender_register_tic:0.6f}s...")
                            os_position = tender_quantiy
                            order_book = self.get_nbbo("THOR_M","THOR_A","bids")
                            # print(order_book)
                            # print(f'order book 2:{order_book}') ##Line for debugging
                            ##run down the order book from the top
                            print(f"recall order book takes: {tender_register_toc-time.perf_counter():0.6f}s")
                            limit_order_tic = time.perf_counter()
                            for order in order_book:
                                print('next order book',os_position,order['quantity'] - order['quantity_filled'])
                                if (os_position > 0) & (os_position>=(order['quantity'] - order['quantity_filled'])) & (order['quantity'] - order['quantity_filled'] > 0):
                                    # print('sell logic 1') ##Line for debugging
                                    order_req = self.insert_order(order['ticker'],(order['quantity']-order['quantity_filled']),"LIMIT","SELL",tender_price+price_epsilon)
                                    os_position -= order['quantity']-order['quantity_filled']
                                    print(f"{os_position} remaining to fill")
                                    self.wait(0.05)
                                elif (os_position > 0) & (os_position<(order['quantity'] - order['quantity_filled'])) & (order['quantity'] - order['quantity_filled'] > 0):
                                    # print('sell logic 2') ##Line for debugging
                                    order_req = self.insert_order(order['ticker'],os_position,"LIMIT","SELL",tender_price+price_epsilon)
                                    os_position = 0
                                    print(f"{os_position} remaining to fill")
                                    break
                            print(f"All limit orders submitted in {time.perf_counter()-limit_order_tic:0.6f}s") #this is a timer for testing
                            #check os position after complete the order book and fill the rest with MARKET
                            wait_time = 0
                            open_orders_count = 1
                            while (wait_time < 20) & (open_orders_count != 0):
                                self.wait(0.25)
                                open_orders_res = self.get_orders()
                                open_orders = open_orders_res.json()
                                open_orders_count = len(open_orders)
                                limit_order_toc = time.perf_counter()
                                print(f"check open orders: {wait_time+1}, {open_orders_count}")
                                wait_time += 1

                            if (open_orders_count != 0) | (os_position != 0):
                                print('There are still unfilled limit orders; These orders will be cancelled now')
                                for open_order in open_orders:
                                    del_req = self.delete_order(open_order['order_id'])
                                    print(f"Delete order {open_order['order_id']}; Status: {del_req.status_code}")
                                self.wait(1)
                                os_position = self.get_securities(tender_ticker).json()[0]['position']
                                print(f"outstanding: {os_position}")
                                while os_position != 0:
                                    print(f"All order book cleared, {os_position} remaining, fill with market order")
                                    order_book = self.get_nbbo("THOR_M","THOR_A",'bids')
                                    for order in order_book:
                                        print('next order book',os_position,order['quantity'] - order['quantity_filled'])
                                        if (os_position > 0) & (os_position>=(order['quantity'] - order['quantity_filled'])) & (order['quantity'] - order['quantity_filled'] > 0):
                                            # print('sell logic 1') ##Line for debugging
                                            order_req = self.insert_order(order['ticker'],(order['quantity']-order['quantity_filled']),"MARKET","SELL")
                                            os_position -= order['quantity']-order['quantity_filled']
                                            print(f"{os_position} remaining to fill")
                                            self.wait(0.1)
                                        elif (os_position > 0) & (os_position<(order['quantity'] - order['quantity_filled'])) & (order['quantity'] - order['quantity_filled'] > 0):
                                            # print('sell logic 2') ##Line for debugging
                                            order_req = self.insert_order(order['ticker'],os_position,"MARKET","SELL")
                                            os_position = 0
                                            print(f"{os_position} remaining to fill")
                                            break
                                    self.wait(1)
                                    os_position = self.get_securities(tender_ticker).json()[0]['position']
                                print(f"Position flattened by market orders")
                            else:
                                print(f"tender order cleared with limit orders")
                                print(f"All limit orders are filled in {limit_order_toc-limit_order_tic:0.6f}s!!!")
                            
                        else: 
                            execute_tender_status = 0
                            while execute_tender_status != 200:
                                execute_tender_req = self.execute_tender(tender_id,False)
                                execute_tender_status = execute_tender_req.status_code
                            print(f"Reject tender offer")
                            print(f"Tender Offer execution status: {execute_tender_status}; RIT confirmation message: {execute_tender_req.json()}")

                    elif tender_action == "SELL":
                        live_orders = self.get_nbbo("THOR_M","THOR_A","asks")
                        remaining_fill = tender_quantiy
                        profitable_volume = 0
                        profit = 0
                        for order in live_orders:
                            if  remaining_fill >= order['quantity'] - order['quantity_filled']:
                                profit += (order['quantity'] - order['quantity_filled']) * (order['price'] - tender_price) * -1
                                remaining_fill = remaining_fill - (order['quantity'] - order['quantity_filled'])
                            else:
                                profit += remaining_fill * (order['price'] - tender_price) * -1
                                remaining_fill = 0
                                break
                        print(f"safety margin: {profit}")
                        print(f"safety volume: {profitable_volume}")
                        # print(f"{live_orders}") ##This line is for debugging
                        if profit > safety_margin:
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
                                self.wait(0.1)
                            tender_register_toc = time.perf_counter()
                            print(f"Tender registered in {tender_register_toc - tender_register_tic:0.6f}s...")
                            os_position = tender_quantiy
                            order_book = self.get_nbbo("THOR_M","THOR_A","asks")
                            # print(order_book)
                            # print(f'order book 2:{order_book}') ##Line for debugging
                            ##run down the order book
                            print(f"recall order book takes: {tender_register_toc-time.perf_counter():0.6f}s")
                            limit_order_tic = time.perf_counter()
                            for order in order_book:
                                print('next order book',os_position,order['quantity'] - order['quantity_filled'])
                                if (os_position > 0) & (os_position>=(order['quantity'] - order['quantity_filled'])) & (order['quantity'] - order['quantity_filled'] > 0):
                                    # print('buy logic 1') ##Line for debugging
                                    order_req = self.insert_order(order['ticker'],(order['quantity']-order['quantity_filled']),"LIMIT","BUY",tender_price-price_epsilon)
                                    os_position -= order['quantity']-order['quantity_filled']
                                    print(f"{os_position} remaining to fill")
                                    self.wait(0.05)
                                elif (os_position > 0) & (os_position<(order['quantity'] - order['quantity_filled'])) & (order['quantity'] - order['quantity_filled'] > 0):
                                    # print('buy logic 2') ##Line for debugging
                                    order_req = self.insert_order(order['ticker'],os_position,"LIMIT","BUY",tender_price-price_epsilon)
                                    os_position = 0
                                    print(f"{os_position} remaining to fill")
                                    break
                            print(f"All limit orders submitted in {time.perf_counter()-limit_order_tic:0.6f}s") #this is a timer for testing
                            ##check os position after complete the order book and fill the rest with MARKET
                            wait_time = 0
                            open_orders_count = 1
                            while (wait_time < 20) & (open_orders_count != 0):
                                self.wait(0.25)
                                open_orders_res = self.get_orders()
                                open_orders = open_orders_res.json()
                                open_orders_count = len(open_orders)
                                limit_order_toc = time.perf_counter()
                                print(f"check open orders: {wait_time+1}, {open_orders_count}")
                                wait_time += 1

                            if (open_orders_count != 0) | (os_position != 0):
                                print('There are still unfilled limit orders; These orders will be cancelled now')
                                for open_order in open_orders:
                                    del_req = self.delete_order(open_order['order_id'])
                                    print(f"Delete order {open_order['order_id']}; Status: {del_req.status_code}")
                                self.wait(1)
                                os_position = (self.get_securities(tender_ticker).json()[0]['position'])*-1
                                print(f"outstanding: {os_position}")
                                while os_position != 0:
                                    print(f"All order book cleared, {os_position} remaining, fill with market order")
                                    order_book = self.get_nbbo("THOR_M","THOR_A",'asks')
                                    for order in order_book:
                                        print('next order book',os_position,order['quantity'] - order['quantity_filled'])
                                        if (os_position > 0) & (os_position>=(order['quantity'] - order['quantity_filled'])) & (order['quantity'] - order['quantity_filled'] > 0):
                                            # print('sell logic 1') ##Line for debugging
                                            order_req = self.insert_order(order['ticker'],(order['quantity']-order['quantity_filled']),"MARKET","BUY")
                                            os_position -= order['quantity']-order['quantity_filled']
                                            print(f"{os_position} remaining to fill")
                                            self.wait(0.1)
                                        elif (os_position > 0) & (os_position<(order['quantity'] - order['quantity_filled'])) & (order['quantity'] - order['quantity_filled'] > 0):
                                            # print('sell logic 2') ##Line for debugging
                                            order_req = self.insert_order(order['ticker'],os_position,"MARKET","BUY")
                                            os_position = 0
                                            print(f"{os_position} remaining to fill")
                                            break
                                    self.wait(1)
                                    os_position = (self.get_securities(tender_ticker).json()[0]['position'])*-1
                                print(f"Position flattened by market orders")
                            else:
                                print(f"tender order cleared with limit orders")
                                print(f"All limit orders are filled in {limit_order_toc-limit_order_tic:0.6f}s!!!")

                                                            
                                
                        else: 
                            execute_tender_status = 0
                            while execute_tender_status != 200:
                                execute_tender_req = self.execute_tender(tender_id,False)
                                execute_tender_status = execute_tender_req.status_code
                            print(f"Reject tender offer")
                            print(f"Tender Offer execution status: {execute_tender_status}; RIT confirmation message: {execute_tender_req.json()}")
            
            else:
                if (case['ticks_per_period']-case['tick']) / 10 == (case['ticks_per_period']-case['tick']) // 10:
                    print(f"No tender order, {case['ticks_per_period']-case['tick']} seconds remaining")

            self.wait(self.refresh_rate)
            self.rit_status = rit_status_map[case['status']]

    def var(self,step=10,mode='news'):
        self.wait(0.9)
        self.insert_order('US',2950,'MARKET','BUY')
        self.wait(0.1)
        self.insert_order('BRIC',2950,'MARKET','BUY')
        self.wait(0.1)
        self.insert_order('BOND',2950,'MARKET','BUY')
        self.wait(0.1)

        e1 = 0.0835/252
        e2 = 0.1489/252
        e3 = 0.0582/252

        sig1 = 0.2085/(252**0.5)
        sig2 = 0.2524/(252**0.5)
        sig3 = 0.0869/(252**0.5)

        rho12 = 0.48
        rho13 = 0.068
        rho23 = 0.005

        x = step
        
        while self.rit_status == 1:
            case_res = self.get_case()
            case = case_res.json()

            holdings = []

            for i in ['US','BRIC','BOND','CASH']:
                _holding_res = self.get_securities(i)
                _holding_data = _holding_res.json()

                _holding = {
                    'ticker':i,
                    'volume': _holding_data[0]['position'],
                    'last': _holding_data[0]['last'],
                    'mtm': _holding_data[0]['position']*_holding_data[0]['last']
                }
                holdings.append(_holding.copy())
            
            print('holdings')
            print(holdings)
            
            port_value = sum([holding['mtm'] for holding in holdings])

            for holding in holdings:
                holding['weight'] = holding['mtm']/port_value

            var = self.calc_var(holdings[0]['weight'],holdings[1]['weight'],holdings[2]['weight'],e1,e2,e3,sig1,sig2,sig3,rho12,rho13,rho23) * port_value * -1

            print(f'portfolio value: {port_value}')
            print(f'99% var: {var}')
            
            news_res = self.get_news()
            news = news_res.json()


            if mode == 'naive':
                if var > 19900:
                    self.insert_order('US',5*x,'MARKET','SELL')
                    self.wait(0.1)
                    self.insert_order('BRIC',5*x,'MARKET','SELL')
                    self.wait(0.1)
                    self.insert_order('BOND',((50*holdings[0]['last']+50*holdings[1]['last'])/holdings[2]['last'])-1,'MARKET','BUY')
                    self.wait(0.1)
                elif var < 18900:
                    self.insert_order('BOND',100,'MARKET','SELL')
                    self.wait(0.1)
                    self.insert_order('US',50,'MARKET','BUY')
                    self.wait(0.1)
                    self.insert_order('BRIC',((100*holdings[2]['last']-50*holdings[0]['last'])/holdings[1]['last'])-1,'MARKET','BUY')
                    self.wait(0.1)
            else:
                if len(news) == 1:
                    if var > 19900:
                        self.insert_order('US',5*x,'MARKET','SELL')
                        self.wait(0.1)
                        self.insert_order('BRIC',5*x,'MARKET','SELL')
                        self.wait(0.1)
                        self.insert_order('BOND',((5*x*holdings[0]['last']+5*x*holdings[1]['last'])/holdings[2]['last'])-1,'MARKET','BUY')
                        self.wait(0.1)
                    elif var < 18900:
                        self.insert_order('BOND',10*x,'MARKET','SELL')
                        self.wait(0.1)
                        self.insert_order('US',5*x,'MARKET','BUY')
                        self.wait(0.1)
                        self.insert_order('BRIC',((10*x*holdings[2]['last']-5*x*holdings[0]['last'])/holdings[1]['last'])-1,'MARKET','BUY')
                        self.wait(0.1)
                else:
                    last_news = news[0]
                    last_news_body = last_news['body'].split("=")
                    print("news")
                    print(last_news['body'])
                    print(last_news_body)
                    us_target = float(last_news_body[1].split("<")[0][2:])
                    bric_target = float(last_news_body[2].split("<")[0][2:])
                    bond_target = float(last_news_body[2].split(">")[1][5:])
                    print(f'target price: {us_target},{bric_target},{bond_target}')
                    us_return = us_target/holdings[0]['last'] - 1
                    bric_return = bric_target/holdings[1]['last'] - 1
                    bond_return = bond_target/holdings[2]['last'] - 1
                    print(f'target return: {us_return},{bric_return},{bond_return}')

                    if max(us_return,bric_return,bond_return) == us_return:
                        if (var < 19900) & (var > 18000):
                            print('US return highest')
                            self.insert_order('BRIC',10*x,'MARKET','SELL')
                            self.insert_order('BOND',2*x,'MARKET','BUY')
                            self.insert_order('US',((10*x*holdings[1]['last']-2*x*holdings[2]['last'])/holdings[0]['last']),'MARKET','BUY')
                            self.wait(0.1)
                        elif (var <= 18000):
                            if max(bric_return,bond_return) == bric_return:
                                self.insert_order('BOND',10*x,'MARKET','SELL')
                                self.insert_order('US',((10*x*holdings[2]['last'])/holdings[0]['last']),'MARKET','BUY')
                            else:
                                self.insert_order('BRIC',10*x,'MARKET','SELL')
                                self.insert_order('US',((10*x*holdings[1]['last'])/holdings[0]['last']),'MARKET','BUY')
                            self.wait(0.1)
                        else:
                            print('Adjust down var')
                            if holdings[1]['volume'] > 0:
                                self.insert_order('US',10*x,'MARKET','SELL')
                                self.insert_order('BRIC',20*x,'MARKET','SELL')
                                self.insert_order('BOND',((10*x*holdings[0]['last']+20*x*holdings[1]['last'])/holdings[2]['last']),'MARKET','BUY')
                            else:
                                self.insert_order('BRIC',10*x,'MARKET','SELL')
                                self.insert_order('BRIC',20*x,'MARKET','BUY')
                                self.insert_order('BOND',((-10*x*holdings[0]['last']+20*x*holdings[1]['last'])/holdings[2]['last']),'MARKET','SELL')
                            self.wait(0.1)
                    
                    elif max(us_return,bric_return,bond_return) == bric_return:
                        if (var < 19900) & (var > 18000):
                            print('BRIC return highest')
                            self.insert_order('US',10*x,'MARKET','SELL')
                            self.insert_order('BOND',4*x,'MARKET','BUY')
                            self.insert_order('BRIC',((10*x*holdings[0]['last']-4*holdings[2]['last'])/holdings[1]['last']),'MARKET','BUY')
                            self.wait(0.1)
                        elif var <= 18000:
                            if max(us_return,bond_return) == us_return:
                                self.insert_order('BOND',10*x,'MARKET','SELL')
                                self.insert_order('BRIC',((10*x*holdings[2]['last'])/holdings[0]['last']),'MARKET','BUY')
                            else:
                                self.insert_order('US',10*x,'MARKET','SELL')
                                self.insert_order('BRIC',((10*x*holdings[0]['last'])/holdings[0]['last']),'MARKET','BUY')
                            self.wait(0.1)
                        else:
                            print('Adjust down var')
                            if holdings[0]['volume'] > 0:
                                self.insert_order('US',20*x,'MARKET','SELL')
                                self.insert_order('BRIC',10*x,'MARKET','SELL')
                                self.insert_order('BOND',((20*x*holdings[0]['last']+10*x*holdings[1]['last'])/holdings[2]['last']),'MARKET','BUY')
                            else:
                                self.insert_order('US',20*x,'MARKET','BUY')
                                self.insert_order('BRIC',10*x,'MARKET','SELL')
                                self.insert_order('BOND',((20*x*holdings[0]['last']-10*x*holdings[1]['last'])/holdings[2]['last']),'MARKET','SELL')
                            self.wait(0.1)
                        
                    else:
                        print('BOND return highest')
                        if max(us_return,bric_return) == us_return:
                            if holdings[0]['volume'] < 0:
                                self.insert_order('US',4*x,'MARKET','BUY')
                                self.insert_order('BRIC',6*x,'MARKET','SELL')
                                self.insert_order('BOND',((-4*x*holdings[0]['last']+6*x*holdings[1]['last'])/holdings[2]['last']),'MARKET','BUY')
                            elif holdings[1]['volume'] < 0:
                                self.insert_order('US',6*x,'MARKET','SELL')
                                self.insert_order('BRIC',4*x,'MARKET','BUY')
                                self.insert_order('BOND',((6*x*holdings[0]['last']-4*x*holdings[1]['last'])/holdings[2]['last']),'MARKET','BUY')
                            else:
                                self.insert_order('US',3*x,'MARKET','SELL')
                                self.insert_order('BRIC',7*x,'MARKET','SELL')
                                self.insert_order('BOND',((3*x*holdings[0]['last']+7*x*holdings[1]['last'])/holdings[2]['last']),'MARKET','BUY')
                        else:
                            if holdings[0]['volume'] < 0:
                                self.insert_order('US',4*x,'MARKET','BUY')
                                self.insert_order('BRIC',6*x,'MARKET','SELL')
                                self.insert_order('BOND',((-4*holdings[0]['last']+6*holdings[1]['last'])/holdings[2]['last']),'MARKET','BUY')
                            elif holdings[1]['volume'] < 0:
                                self.insert_order('US',6*x,'MARKET','SELL')
                                self.insert_order('BRIC',4*x,'MARKET','BUY')
                                self.insert_order('BOND',((6*holdings[0]['last']-4*holdings[1]['last'])/holdings[2]['last']),'MARKET','BUY')
                            else:
                                self.insert_order('US',6*x,'MARKET','SELL')
                                self.insert_order('BRIC',4*x,'MARKET','SELL')
                                self.insert_order('BOND',((6*holdings[0]['last']+4*holdings[1]['last'])/holdings[2]['last']),'MARKET','BUY')
                        self.wait(0.1)
            
            print("rebalance done")

            holdings = []

            for i in ['US','BRIC','BOND','CASH']:
                _holding_res = self.get_securities(i)
                _holding_data = _holding_res.json()
                _holding = {
                    'ticker':i,
                    'volume': _holding_data[0]['position'],
                    'last': _holding_data[0]['last'],
                    'mtm': _holding_data[0]['position']*_holding_data[0]['last']
                }
                holdings.append(_holding.copy())
            
            port_value = sum([holding['mtm'] for holding in holdings])

            for holding in holdings:
                holding['weight'] = holding['mtm']/port_value
            
            var = self.calc_var(holdings[0]['weight'],holdings[1]['weight'],holdings[2]['weight'],e1,e2,e3,sig1,sig2,sig3,rho12,rho13,rho23) * port_value * -1

            print(f'after rebalance portfolio value: {port_value}')
            print(f'after rebalance 99% var: {var}')

            self.rit_status = rit_status_map[case['status']]
            self.wait(self.refresh_rate)
            
            


            
        


    #######################################
    #######################################
    #######################################