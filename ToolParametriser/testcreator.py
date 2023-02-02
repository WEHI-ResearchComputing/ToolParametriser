from abc import ABC, abstractmethod
from datetime import datetime
import csv
import random,os
import logging,glob,shutil,errno
from string import Template
import xml.etree.ElementTree as ET

class AbstractTester(ABC):
    def __init__(self,config:dict) -> None:
        super().__init__()
        self.tmplfile="" #Must be set by concrete class
        self.Config=config
        if self.validate_config():
            self.Config["Output_path"] = config['output']['path']+"_"+datetime.now().strftime('%Y%m%d%H%M%S')
            self.get_test_parameters()
        else:
            logging.fatal("Config file not valid")
            raise InvalidConfigObject
        if not os.path.exists(f'{os.path.expanduser("~")}/.toolparametriser/'):
            os.makedirs(f'{os.path.expanduser("~")}/.toolparametriser/')
        
        FORMAT = '[%(asctime)s]:%(levelname)s:%(name)s:%(message)s'
        logging.basicConfig(format=FORMAT,filename=f'{os.path.expanduser("~")}/.toolparametriser/debug.log', 
                    encoding='utf-8', level=logging.DEBUG)
    
        self.template_path=f"{os.path.expanduser('~')}/.toolparametriser/"
    
    @abstractmethod
    def create_jobscript_template(self,**kwargs):
        pass
        
    @abstractmethod
    def run(self,runID:str,parameters:dict):
        pass
    
    def run_jobscript(self,parameters:dict,runID:str):
        #Prepare values for tmpl
        config=self.Config
        ntasks=1
        if 'ntasks'  in parameters.keys():
            ntasks=parameters["ntasks"]
        
        params={
            'partition': parameters["partition"], 
            'type': parameters["type"], 
            'jobname': parameters["jobname"], 
            'numfiles': parameters["numfiles"], 
            'cpuspertask': parameters["cpuspertask"], 
            'mem': parameters["mem"], 
            'threads': parameters["threads"], 
            'timelimit':parameters["timelimit"],
            'ntasks':ntasks,
            'email':config["jobs"]["email"]
        }

        params['constraint']=None
        if 'constraint'  in parameters.keys():
            params['constraint']=parameters['constraint']
                
        ##Substitute Tmpl 
        with open(self.tmplfile, 'r') as f:
            template = Template(f.read())
            result = template.safe_substitute(params)
        ##Save to file
        with open(os.path.join(self.Config["Output_path"],runID,"batch.slurm"), 'w') as f:
            f.write(result)
        ##RUN
        print(
            os.system(f"cd {os.path.join(self.Config['Output_path'],runID)};"+ 
                f"sbatch {os.path.join(self.Config['Output_path'],runID,'batch.slurm')}")
            )

    ##TODO validate_config
    def validate_config(self)->bool:
        print("Validated")
        return True

    ##TODO validate_test_parameters
    def validate_test_parameters(self)->bool:
        return True

    def get_test_parameters(self):
        try:
            with open(self.Config['jobs']['params_path'], "r") as file:
                self.Config["job_parameters"]=list(csv.DictReader(file))
        except IOError:
            if IOError.errno == errno.EACCES:
                logging.fatal("Test parameters file exists, but isn't readable")
            elif IOError.errno == errno.ENOENT:
                logging.fatal("Test parameters file isn't readable because it isn't there")
    
    
    def prepare_run_dir(self,runID:str,params:dict):
        outpath=os.path.join(self.Config["Output_path"],runID)
        os.makedirs(outpath)
        allinputfiles = glob.glob(self.Config['input']['path'], recursive=False)
        runfiles = random.sample(allinputfiles, k=int(params["numfiles"]))
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

    
    def run_test(self,usetmpl:bool):
        self.get_test_parameters()

        if self.validate_test_parameters():
            for parameters in self.Config["job_parameters"]:
                runID = f"repo-{parameters['jobname']}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                self.prepare_run_dir(runID=runID,params=parameters)
                if (not os.path.exists(self.tmplfile)) or (not usetmpl):
                    self.create_jobscript_template()
                self.run(runID,parameters)
        else:
            logging.fatal("Test Parameters file not valid.")
            raise InvalidTestParameters

    

class MQTester(AbstractTester):
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.tmplfile=os.path.join(self.template_path,"MQtemplate.tmpl")
    
    def run(self,runID,parameters):
        self.update_xml(runID ,parameters)
        self.run_jobscript(parameters,runID)
        print("MQ created and run")

    def create_jobscript_template(self):
        print("Creating new tmpl")
        with open(self.tmplfile, "w+") as fb:
            fb.writelines("#!/bin/bash\n")
            fb.writelines("#SBATCH -p ${partition}\n")
            fb.writelines("#SBATCH --job-name=${jobname}\n")
            fb.writelines("#SBATCH --ntasks=${ntasks}\n")
            fb.writelines("#SBATCH --time=${timelimit}\n")
            fb.writelines("#SBATCH --cpus-per-task=${cpuspertask}\n")
            fb.writelines("#SBATCH --mem=${mem}G\n")
            fb.writelines("#SBATCH --output=slurm-%j.out\n")
            fb.writelines("#SBATCH --mail-type=ALL,ARRAY_TASKS\n")
            fb.writelines("#SBATCH --mail-user=${email}\n")
           
            fb.writelines("#SBATCH --constraint=${constraint}\n")

            fb.writelines("module load MaxQuant/2.0.2.0\n")
            fb.writelines("/stornext/System/data/apps/rc-tools/rc-tools-1.0/bin/tools/MQ/createMQXML.py ${threads}\n")
            fb.writelines("MaxQuant mqpar.mod.xml\n")

            fb.writelines(
                'echo \"$SLURM_ARRAY_JOB_ID,$SLURM_ARRAY_TASK_ID,${partition},${type},${jobname},${numfiles},${cpuspertask},${mem},${threads},${timelimit}\" >> '+f'{self.Config["Output_path"]}/jobs_executed.txt\n'
            )

    def validate_config(self) -> bool:
        valid = super().validate_config()
        if not any(d.get('name', "") == 'xml' for d in self.Config["extra"]) or not any(d.get('name', "") == 'fasta' for d in self.Config["extra"]):
            valid=False
        if not self.Config["jobs"]["tool_type"]=="MQ":
            valid=False
        return valid

    """
    Method specific to MQ only, to update XML file
    """   
    def update_xml(self,runID:str,parameters:dict) -> None:
        xml_path=next(item['path'] for item in self.Config["extra"] if item["name"] == "xml")
        if not os.path.exists(xml_path):
            logging.error(f"No xml file found.")
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), xml_path)
        else:
            tree = ET.parse(xml_path)
            outputfile=os.path.join(self.Config["Output_path"],runID,"mqpar.mod.xml")
            root = tree.getroot()
            numfiles=0
            for filepath_tag in root.findall('filePaths/string'):
                winpath=filepath_tag.text
                if winpath != None:
                    linuxpath=os.path.join(self.Config["Output_path"],runID,winpath.split("\\")[-1])
                    if(os.path.exists(linuxpath)):
                        logging.debug(f"{linuxpath} exists")
                        filepath_tag.text=linuxpath
                        logging.info(f"Updating filepath : {linuxpath}")
                        numfiles=numfiles+1
                    else:
                        root.findall('filePaths')[0].remove(filepath_tag)
            logging.info(f"Updated {numfiles} files.")
            winfastapath=root.findall('fastaFiles/FastaFileInfo/fastaFilePath')[0].text
            if winfastapath != None:
                linuxfastapath=os.path.join(os.path.abspath(os.getcwd()),winfastapath.split("\\")[-1])
            
                logging.info(f"Updating fastapath : {linuxfastapath}")
                if(os.path.exists(linuxfastapath)):
                        root.findall('fastaFiles/FastaFileInfo/fastaFilePath')[0].text=linuxfastapath
            
            #<useDotNetCore>True</useDotNetCore>
            root.findall('useDotNetCore')[0].text="True"
            #<numThreads>8</numThreads>
            numthreads=parameters["threads"]
            numthreads = numfiles if (numfiles != 0) and (numthreads==0) else numthreads
            root.findall('numThreads')[0].text=str(numthreads)
            logging.info(f"Threads set to {numthreads}.")
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

class DiaNNTester(AbstractTester):
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.tmplfile=os.path.join(self.template_path,"DiaNNtemplate.tmpl")

    def create_jobscript_template(self):
        pass

    def create_jobscript(self)->bool:
        pass

        return True