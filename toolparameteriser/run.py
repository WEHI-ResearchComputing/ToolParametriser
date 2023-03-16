import errno
import toolparameteriser.testcreator
import toolparameteriser.testresults
import toolparameteriser.utils
import tomllib
import logging,os
import argparse
toolparameteriser.utils.setlogging()

def main(args=None):

    if not args:
        parser = argparse.ArgumentParser(description='Run/analyse a tool test')
        parser.add_argument('-c','--config_path', metavar='path', required=True,
                            help='the path to configuration file')
        parser.add_argument('-D','--dryrun', required=False, default = False, action = 'store_true', 
                           help='if present jobs will not run')
        parser.add_argument('-R','--runtype', metavar="str", required=True,
                           help='can be either [run, analyse]')
                           
        args = parser.parse_args()

    try:           
        with open(args.config_path, "rb") as f:
            config = tomllib.load(f)
            logging.info("Successfully parsed config file, {fname}".format(fname=args.config_path))

    except IOError as e:
        match e.errno:
            case errno.EACCES:
                logging.fatal("Config file, {fname} exists, but isn't readable".format(fname=args.config_path))
                exit()
            case errno.ENOENT:
                logging.fatal("Config file, {fname} isn't readable because it isn't there".format(fname=args.config_path))
                exit()
            case _:
                logging.fatal(f"Config file error: {str(e)}")
                exit()
    
    config["dryrun"] = args.dryrun

    if args.runtype.lower()=="run":
        match config["jobs"]["tool_type"].lower():
            case "diann":
                test=toolparameteriser.testcreator.DiaNNTester(config=config)
            case "mq":
                test=toolparameteriser.testcreator.MQTester(config=config) 
            case _:
                test=toolparameteriser.testcreator.FromCMDTester(config=config)
        test.run_test()

    elif args.runtype.lower()=="analyse":
        logging.info("Analysing completed jobs.....")
        jobs_completed_file=config['output']['jobs_details_path']
        if 'results_file' not in config['output']:
            config['output']['result_file']="./allresults.csv"
        toolparameteriser.testresults.get(completed_jobs=jobs_completed_file,results_path=config['output']['results_file'])
    else:
        logging.fatal("Run Type (-R) Unkown, valid values include [run, analyse]")


if __name__ == "__main__":
    
    main()
