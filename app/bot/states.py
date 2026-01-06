from aiogram.fsm.state import State, StatesGroup

class AddTracker(StatesGroup):
    kind = State()
    crypto_query = State()
    choose_coin = State()
    quote = State()
    fx_base = State()
    fx_quote = State()
    direction = State()
    target = State()
class Rate(StatesGroup):
    kind = State()
    crypto_query = State()
    choose_coin = State()
    quote = State()
    fx_base = State()
    fx_quote = State()