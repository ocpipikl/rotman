# %%
from rit_lib import rit

# %%
counter = 0
while counter < 100:
    case = rit(mode='auto')
    counter += 1
# %%
rit.insert_order('BRIC',2900,'MARKET','BUY')
# %%
a = rit(mode='debug')

#%%
a.insert_order('BRIC',2900,'MARKET','BUY')
# %%
87000 in range(87000,87001)
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