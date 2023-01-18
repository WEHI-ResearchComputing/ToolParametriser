from abc import ABC, abstractmethod
from datetime import datetime
import csv
import random,os
import logging,glob,shutil,errno
import xml.etree.ElementTree as ET

class AbstractTester(ABC):
    def __init__(self,config:dict) -> None:
        super().__init__()
        self.Config=config
        if self.validate_config():
            self.Config["Output_path"] = config['output']['path']+"_"+datetime.now().strftime('%Y%m%d%H%M%S')
            self.get_test_parameters()
        else:
            logging.fatal("Config file not valid")
            raise InvalidConfigObject

    def validate_config(self)->bool:
        print("Validated")
        return True
    
    def validate_test_parameters(self)->bool:
        return True

    def get_test_parameters(self):
        try:
            with open(self.Config['jobs']['params_path'], "r") as file:
                self.Config["job_parameters"]=list(csv.DictReader(file))
        except IOError as e:
            if e.errno == errno.EACCES:
                logging.fatal("Test parameters file exists, but isn't readable")
            elif e.errno == errno.ENOENT:
                logging.fatal("Test parameters file isn't readable because it isn't there")
    
    
    def prepare_run_dir(self,runID:str,params:dict):
        outpath=os.path.join(self.Config["Output_path"],runID)
        os.makedirs(outpath)
        allinputfiles = glob.glob(self.Config['input']['path'], recursive=False)
        runfiles = random.sample(allinputfiles, k=int(params["NumFiles"]))
        for runfile in runfiles:
            name_of_folder = runfile.split("/")[-1]
            try:
                shutil.copytree(runfile, 
                            os.path.join(outpath,name_of_folder), 
                            dirs_exist_ok=True)
            except NotADirectoryError:
                shutil.copy(runfile, os.path.join(outpath,name_of_folder))
        for extrafile in self.Config["extra"]:
            shutil.copy(extrafile["path"],outpath)

    
    def run_test(self):
        self.get_test_parameters()
        if self.validate_test_parameters():
            for parameters in self.Config["job_parameters"]:
                runID = f"repo-{parameters['job-name']}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                self.prepare_run_dir(runID=runID,params=parameters)
                self.create_run(parameters)
        else:
            logging.fatal("Test Parameters file not valid.")
            raise InvalidTestParameters

    @abstractmethod
    def create_run(self,parameters:dict):
        pass

class MQTester(AbstractTester):
    def __init__(self, config: dict) -> None:
        super().__init__(config)
    
    def create_run(self,parameters):
        print(parameters)
        self.updateXmlFile(parameters)
        print("MQ created and run")

    def validate_config(self) -> bool:
        valid = super().validate_config()
        if not any(d.get('name', "") == 'xml' for d in self.Config["extra"]) or not any(d.get('name', "") == 'fasta' for d in self.Config["extra"]):
            valid=False
        if not self.Config["jobs"]["tool_type"]=="MQ":
            valid=False
        return valid
    """
    Method specific to MQ, to update XML file
    """   
    def update_xml(self,parameters:dict) -> None:
        xml_path=next(item['path'] for item in self.Config["extra"] if item["name"] == "xml")
        if not os.path.exists(xml_path):
            logging.error(f"No xml file found.")
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), xml_path)
        else:
            tree = ET.parse(xml_path)
            outputfile=os.path.join(runfile.split("/")[-1],"mqpar.mod.xml")
            root = tree.getroot()

            numfiles=0
            for filepath_tag in root.findall('filePaths/string'):
                winpath=filepath_tag.text
                linuxpath=os.path.join(os.path.abspath(os.getcwd()),winpath.split("\\")[-1])
                if(os.path.exists(linuxpath)):
                    filepath_tag.text=linuxpath
                    logging.info(f"Updating filepath : {linuxpath}")
                    numfiles=numfiles+1
                else:
                    root.findall('filePaths')[0].remove(filepath_tag)
            numthreads=parameters["threads"]
            numthreads = numfiles if (numfiles != 0) and (numthreads==0) else numthreads
    
            logging.info(f"{numthreads},{numfiles}")  
            
            winfastapath=root.findall('fastaFiles/FastaFileInfo/fastaFilePath')[0].text
            linuxfastapath=os.path.join(os.path.abspath(os.getcwd()),winfastapath.split("\\")[-1])
            
            logging.info(f"Updating fastapath : {linuxfastapath}")
            if(os.path.exists(linuxfastapath)):
                    root.findall('fastaFiles/FastaFileInfo/fastaFilePath')[0].text=linuxfastapath
            
            #<useDotNetCore>True</useDotNetCore>
            root.findall('useDotNetCore')[0].text="True"
            #<numThreads>8</numThreads>
            root.findall('numThreads')[0].text=str(numthreads)
            
            logging.info(f"Saving new xml file : {outputfile}")
            tree.write(outputfile)

class InvalidConfigObject(Exception):
    "Raised when config object is not valid, or have missing fields"
    def __init__(self, message="Config object is not valid, or have missing fields. See logs in ~/.toolparametriser/"):
        self.message = message
        super().__init__(self.message)
class InvalidTestParameters(Exception):
    "Raised when Test Parameters file is not valid, or have missing fields"
    def __init__(self, message="Test Parameters file is not valid, or have missing fields. See logs in ~/.toolparametriser/"):
        self.message = message
        super().__init__(self.message)
    