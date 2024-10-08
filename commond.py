# from logind import current_user
# print(current_user)

current_user = None

def set_current_user(username):
    global current_user
    current_user = username

def get_current_user():
    return current_user