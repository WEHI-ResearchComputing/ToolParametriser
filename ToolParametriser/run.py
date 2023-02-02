import testcreator
import tomllib
import logging,os,errno

if not os.path.exists(f'{os.path.expanduser("~")}/.toolparametriser/'):
    os.makedirs(f'{os.path.expanduser("~")}/.toolparametriser/')

config_path="/vast/scratch/users/iskander.j/ToolParametriser/examples/configMQ.toml"
if not os.path.exists(config_path):
    logging.fatal("Config file does not exit")
    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_path)
        
with open(config_path, "rb") as f:
    config = tomllib.load(f)   
    #print(config)

mq=testcreator.MQTester(config=config)
mq.run_test(usetmpl=False)