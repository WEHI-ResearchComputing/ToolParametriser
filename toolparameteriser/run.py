import errno
import toolparameteriser.testcreator
import toolparameteriser.testresults
import toolparameteriser.utils
import tomllib
import logging,os
import argparse

def main(args=None):

    if not args:
        parser = argparse.ArgumentParser(description='Run/analyse a tool test')
        parser.add_argument('-c','--config_path', metavar='path', required=True,
                            help='the path to configuration file')
        parser.add_argument('-D','--dryrun', action = 'store_true', 
                           help='if present jobs will not run')
        parser.add_argument('-R','--runtype', metavar="str", required=True,
                           help='can be either [run, analyse]')
        parser.add_argument('-d','--debug', action='store_true',
                            help='Sets logging level to Debug')
                           
        args = parser.parse_args()

        toolparameteriser.utils.setlogging(args.debug)
        logging.debug("Running with Debug info.")

    try:           
        with open(args.config_path, "rb") as f:
            config = tomllib.load(f)
            logging.info(f"Successfully parsed config file, {args.config_path}")

    except IOError as e:
        match e.errno:
            case errno.EACCES:
                logging.fatal(f"Config file, {args.config_path} exists, but isn't readable")
                exit()
            case errno.ENOENT:
                logging.fatal(f"Config file, {args.config_path} isn't readable because it isn't there")
                exit()
            case _:
                logging.fatal(f"Config file error: {str(e)}")
                exit()
    
    config["dryrun"] = args.dryrun
    config["debug"] = args.debug

    if args.runtype.lower()=="run":
        match config["jobs"]["tool_type"].lower():
            case "diann":
                test=toolparameteriser.testcreator.DiaNNTester(config=config)
            case "mq":
                test=toolparameteriser.testcreator.MQTester(config=config) 
            case _:
                test=toolparameteriser.testcreator.FromCMDTester(config=config)

        logging.info("Beginning run.....")
        test.run_test()

    elif args.runtype.lower()=="analyse":
        logging.info("Analysing completed jobs.....")
        jobs_completed_file=config['output']['jobs_details_path']
        if 'results_file' not in config['output']:
            config['output']['result_file']="./allresults.csv"
        toolparameteriser.testresults.get(completed_jobs=jobs_completed_file,results_path=config['output']['results_file'],debug=config["debug"])
    else:
        logging.fatal("Run Type (-R) Unkown, valid values include [run, analyse]")

if __name__ == "__main__":
    
    main()
