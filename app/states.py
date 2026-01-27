from aiogram.fsm.state import State, StatesGroup


class AuthStates(StatesGroup):
    waiting_admin_code = State()
    choosing_role = State()


class CustomerReg(StatesGroup):
    first_name = State()
    last_name = State()
    org_name = State()


class OrderFlow(StatesGroup):
    order_name = State()
    doc_types = State()
    construction_types = State()
    sections_capital = State()
    sections_linear = State()
    description = State()
    deadline = State()
    price = State()
    expertise_required = State()
    files_link = State()
    confirm_save = State()


class ExecutorReg(StatesGroup):
    first_name = State()
    last_name = State()
    org_name = State()
    experience = State()
    resume = State()
    doc_types = State()
    construction_types = State()
    sections_capital = State()
    sections_linear = State()


class RatingState(StatesGroup):
    waiting_review = State()


class HelpState(StatesGroup):
    waiting_text = State()
