#!/stornext/HPCScratch/home/iskander.j/myenvs/py3_11/bin/python

import testcreator
import tomllib
import logging,os,errno
import argparse


def main(config_path,usetmpl):
    print(config_path,usetmpl)
    if not os.path.exists(f'{os.path.expanduser("~")}/.toolparametriser/'):
        os.makedirs(f'{os.path.expanduser("~")}/.toolparametriser/')

    #config_path="/vast/scratch/users/iskander.j/ToolParametriser/examples/configMQ.toml"
    if not os.path.exists(config_path):
        logging.fatal("Config file does not exit")
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_path)
            
    with open(config_path, "rb") as f:
        config = tomllib.load(f)   

    mq=testcreator.MQTester(config=config)
    #mq.run_test(usetmpl=usetmpl)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create a ArcHydro schema')
    parser.add_argument('-c','--config_path', metavar='path', required=True,
                        help='the path to configuration file')
    parser.add_argument('-T','--usetmpl', metavar="bool", required=True,
                        help='whether to use old template if found or create a new one')
    
    args = parser.parse_args()
    main(config_path=args.config_path,usetmpl=args.usetmpl)