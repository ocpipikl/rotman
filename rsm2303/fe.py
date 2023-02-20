# %%
from rit_lib import rit

# %%
counter = 0
while counter < 3:
    case = rit(mode='debug').lt3()
    counter += 1
# %%
