# %%
from rit_lib import rit

# %%
case = rit(mode='auto')

# %%
counter = 0
while counter < 10:
    case = rit(mode='auto')
    counter += 1# %%
case = rit(mode='debug')
# %%
rit.insert_order('BRIC',2900,'MARKET','BUY')
# %%
a = rit(mode='debug')

#%%
a.insert_order('BRIC',2900,'MARKET','BUY')
# %%
order_book_a = case.get_order_book('THOR_A').json()
order_book_m = case.get_order_book('THOR_M').json()

# %%
ask_a = order_book_a['asks']
ask_m = order_book_m['asks']

# %%
m_a = ask_a[0]['price']
m_m = ask_m[0]['price']

# %%
case.get_nbbo('THOR_M','THOR_A','bids')
# %%
case.algo3()
# %%
case.rit_status = 1