

default_credit = 1000

# 单位:秒
update_interval = 1800


Admin_passwd = ""


def ADMIN_PASSWD(passwd: str):
    global Admin_passwd
    Admin_passwd = passwd


def UPDATE_INTERVAL(time: int):
    global update_interval
    update_interval = time


def DEFAULT_CREDIT(credit: int):
    global default_credit
    default_credit = credit
