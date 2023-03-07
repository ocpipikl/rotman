# %%
from rit_lib import rit

# %%
counter = 0
while counter < 3:
    case = rit(mode='debug').lt3()
    counter += 1
# %%
case = rit(mode='auto').var()
# %%
rit.insert_order('BRIC',2900,'MARKET','BUY')
# %%
a = rit(mode='debug')

#%%
a.insert_order('BRIC',2900,'MARKET','BUY')
# %%
