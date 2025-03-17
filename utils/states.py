from aiogram.fsm.state import State, StatesGroup


class RegisterStates(StatesGroup):
    # registration states
    ENTER_NAME = State()
    ENTER_AGE = State()
    ENTER_CITY = State()
    ENTER_COUNTRY = State()
    ENTER_BIO = State()

class SelectedVariant(StatesGroup):
    ENTER_VARIANT = State()
    ENTER_HOTEL = State()
    

class ProfileEditStates(StatesGroup):
    ENTER_DATA = State()


class NoteCreateStates(StatesGroup):
    ENTER_NAME = State()
    ENTER_CONTENT = State()


class NoteEditStates(StatesGroup):
    ENTER_NEW_DATA = State()


class TravelCreateStates(StatesGroup):
    # travel creation states
    ENTER_NAME = State()
    ENTER_DESCRIPTION = State()
    ENTER_SECOND_LOCATION = State()
    ENTER_TIMES = State()


class TravelEditStates(StatesGroup):
    ENTER_NAME = State()
    ENTER_DESCRIPTION = State()
    INVITE_FRIENDS = State()


class LocationEditStates(StatesGroup):
    EDIT_INFO = State()


class LocationCreateStates(StatesGroup):
    ENTER_LOCATIONS = State()
    ENTER_TIMES = State()


class AddFriendsStates(StatesGroup):
    ENTER_CONTACT = State()
