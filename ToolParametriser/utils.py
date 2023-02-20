import logging,sys,os

def setlogging():
    if not os.path.exists(f'{os.path.expanduser("~")}/.toolparametriser/'):
        os.makedirs(f'{os.path.expanduser("~")}/.toolparametriser/')
    FORMAT = '[%(asctime)s]|%(levelname)s|%(name)s|%(message)s'
    
    formatter = logging.Formatter(FORMAT)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(f'{os.path.expanduser("~")}/.toolparametriser/debug.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    

    logging.basicConfig(
    level=logging.DEBUG, 
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=[file_handler,stdout_handler])