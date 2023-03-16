import logging,sys,os

def setlogging(debug=False):
    if not os.path.exists(f'{os.path.expanduser("~")}/.toolparameteriser/'):
        os.makedirs(f'{os.path.expanduser("~")}/.toolparameteriser/')
    FORMAT = '[%(asctime)s]|%(levelname)s|%(name)s|%(message)s'

    if debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    formatter = logging.Formatter(FORMAT)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    stdout_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(f'{os.path.expanduser("~")}/.toolparameteriser/debug.log')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    logging.basicConfig(level=level, 
                        format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
                        handlers=[file_handler,stdout_handler])