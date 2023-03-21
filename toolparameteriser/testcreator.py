from abc import ABC, abstractmethod
from datetime import datetime
import csv,json
import random,os
import logging,glob,shutil,errno
from string import Template
import xml.etree.ElementTree as ET
import toolparameteriser.utils
import subprocess
# 

class AbstractTester(ABC):
    def __init__(self,config:dict) -> None:
        super().__init__()
        self.tmplfile="" #Must be set by concrete class
        self.Config=config

        toolparameteriser.utils.setlogging(self.Config["debug"])

        # Creating output directory
        logging.debug("Checking if output path, {p}, exists.".format(p=self.Config['output']['path']))
        if not os.path.exists(self.Config['output']['path']):
            logging.debug("Output path, {p}, does not exist. Creating.".format(p=self.Config['output']['path']))
            os.makedirs(self.Config['output']['path'])
            logging.debug("Output path, {p}, created succesfully.".format(p=self.Config['output']['path']))
        else:
            logging.debug("Output path, {p}, exists. Not creating.".format(p=self.Config['output']['path']))

        # Initializing completed job list
        self.jobs_completed_file=os.path.join(self.Config['output']['path'],"jobs_completed.csv")
        logging.info("Completed list of jobs will be written to {f}.".format(f=self.jobs_completed_file))
        logging.debug("Checking if completed job list, {f}, exists.".format(f=self.jobs_completed_file))
        if not os.path.exists(self.jobs_completed_file):
            logging.debug("Completed job list, {f}, does not exists. Creating.".format(f=self.jobs_completed_file))
            with open(self.jobs_completed_file,'w+') as f:
                    writer = csv.writer(f)
                    writer.writerow(["jobtype","jobid","partition","numfiles","cpuspertask","mem","threads","timelimit","qos","constraints","workingdir","extra"])
            logging.debug("Completed job list, {f}, created successfully.".format(f=self.jobs_completed_file))
        else:
            logging.debug("Completed job list, {f}, exists. Not creating.".format(f=self.jobs_completed_file))    
        
        # Creating sub output directory
        if self._validate_config():
            self.Config["Output_path"] = os.path.join(config['output']['path'],config['jobs']['tool_type']+"_"+datetime.now().strftime('%Y%m%d%H%M%S'))
            logging.debug("Run-specific output path, {p}, creating.".format(p=self.Config["Output_path"]))
            os.makedirs(self.Config["Output_path"])
            logging.debug("Run-specific output path, {p}, created successfully.".format(p=self.Config["Output_path"]))
            if self._validate_test_parameters():
                self._get_test_parameters()
            else:
                logging.fatal("Test Job parameters not valid")
                exit()
        else:
            logging.fatal("Config file not valid")
            exit()

    @abstractmethod
    def _create_jobscript_template(self,**kwargs):
        pass
    
    def _get_tmpl_values(self,parameters:dict,work_dir:str)->dict:
        config=self.Config

        # initialise parameters with config job parameters
        params = config["jobs"]
        params["workdir"]=work_dir
        # join with job profile parameters (job profile takes precedence)
        params.update(parameters)

        if 'ntasks' not in params.keys():
            params['ntasks'] = 1

        # important that "jobtype" is uniform across all jobs
        params['jobtype'] = f'{config["jobs"]["tool_type"]}_{config["jobs"]["run_type"]}'

        return params

    def _run_job(self,parameters:dict,runID:str,work_dir:str):

        #Prepare values for tmpl
        logging.debug("Preparing parameters for job template.")
        params=self._get_tmpl_values(parameters,work_dir) 
        logging.debug("Successfully prepared job parameters.")

        #Substitute Tmpl 
        logging.debug("Inserting job parameters into job template.")
        with open(os.path.join(self.Config["Output_path"],self.tmplfile), 'r') as f:
            template = Template(f.read())
            result = template.safe_substitute(params)
        logging.debug("Successfully inserted job parameters into job template.")

        #Save to file
        scriptdir = os.path.join(self.Config["Output_path"],runID)
        scriptpath = os.path.join(self.Config["Output_path"],runID,"batch.slurm")
        with open(scriptpath, 'w') as f:
            f.write(result)
        logging.info(f"Saved job script to {scriptpath}.")

        #RUN if not dryrun
        if self.Config["dryrun"]:
            logging.info(f"sbatch --chdir={scriptdir} {scriptpath}")
        else:
            # os.system(f"cd {scriptdir} && " + f"sbatch {scriptpath}")
            msg = subprocess.check_output(["sbatch", f"--chdir={scriptdir}", scriptpath], stderr=subprocess.STDOUT)
            logging.info(msg)
           
    ##TODO validate_config
    def _validate_config(self)->bool:

        return True
    ## TODO validate_test_parameters
    def _validate_test_parameters(self)->bool:

        return True

    def _get_test_parameters(self):
        try:
            with open(self.Config['jobs']['params_path'], "r") as file:
                self.Config["job_parameters"]=list(csv.DictReader(file))
        except IOError as e:
            if e.errno == errno.EACCES:  
                logging.fatal("Test parameters file exists, but isn't readable")
                exit()
            elif e.errno == errno.ENOENT:
                logging.fatal("Test parameters file isn't readable because it isn't there")
                exit()
            else:
                logging.fatal(f"Test parameters file error: {str(e)}")
                exit()
        except Exception as e:
                logging.fatal(f"Test parameters file error: {e}")
                exit()
    
    def __prepare_run_dir(self,runID:str,params:dict) -> str:

        logging.info("Preparing output directory for {id}.".format(id=runID))
        outpath=os.path.join(self.Config["Output_path"],runID)
        os.makedirs(outpath)
        logging.debug("Output directory, {p}, created successfully.".format(p=outpath))

        # testing if user has specified 
        try:
            allinputfiles = glob.glob(self.Config['input']['path'], recursive=False)
        except KeyError:
            # below commented statemnt should be placed in a "pre-screening" function
            logging.info('"Input" not specified in config toml file. Not copying files to output directory.')
            return outpath

        if "numfiles" in params.keys(): 
            numfiles = int(params["numfiles"])
        elif "numfiles" in self.Config["jobs"].keys():
            numfiles = int(self.Config["jobs"]["numfiles"])
        else:
            logging.fatal('"numfiles" parameter not supplied in either the config or job parameters files.')
            exit()

        runfiles = random.sample(allinputfiles, k=numfiles)

        logging.info(f"{numfiles} files are being copied to the input directory.")

        for runfile in runfiles:
            name_of_folder = runfile.split("/")[-1]
            logging.debug("Copying {rf} to {p}.".format(rf=runfile, p=os.path.join(outpath,name_of_folder)))
            try:
                shutil.copytree(runfile, 
                            os.path.join(outpath,name_of_folder), 
                            dirs_exist_ok=True)
            except NotADirectoryError:
                shutil.copy(runfile, os.path.join(outpath,name_of_folder))
            logging.debug("Successfully copied {rf} to {p}.".format(rf=runfile, p=os.path.join(outpath,name_of_folder)))

        if "extra" in self.Config:
            for extrafile in self.Config["extra"]:
                shutil.copy(extrafile["path"],outpath)
                logging.debug("Successfully copied {rf} to {p}.".format(rf=extrafile["path"], p=outpath))

        logging.info("Successfully copied files to input directory.")
        
        return outpath

    #Accessible Function
    def run_test(self):    
        self._create_jobscript_template()    
        if self._validate_test_parameters():
            for parameters in self.Config["job_parameters"]:
                for rep in range(self.Config["jobs"]["num_reps"]):
                    runID = f"repo-{parameters['jobname']}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    outpath=self.__prepare_run_dir(runID=runID,params=parameters)
                    self._run_job(runID=runID,parameters=parameters,work_dir=outpath)
            with open(os.path.join(self.Config["Output_path"],'config.json'), 'w') as cfile:
                cfile.write(json.dumps(self.Config))
        else:
            logging.fatal("Test Parameters file not valid.")
            raise InvalidTestParameters

class MQTester(AbstractTester):
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.tmplfile="MQtemplate.tmpl"
        config["jobs"]["run_type"]=""
    
    def _run_job(self,runID,parameters,work_dir):
        self.__update_xml(runID ,parameters)
        super()._run_job(runID=runID,parameters=parameters,work_dir=work_dir)

    def _create_jobscript_template(self,**kwargs):
        with open(os.path.join(self.Config["Output_path"],self.tmplfile), "w+") as fb:
            
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
            fb.writelines("#SBATCH --qos=${qos}\n")
            fb.writelines("#SBATCH --constraint=${constraints}\n")

            fb.writelines("module load MaxQuant/2.0.2.0\n")
            fb.writelines("/stornext/System/data/apps/rc-tools/rc-tools-1.0/bin/tools/MQ/createMQXML.py ${threads}\n")
            fb.writelines("MaxQuant mqpar.mod.xml\n")

            fb.writelines(
                'echo \"${jobtype},$SLURM_JOB_ID,${partition},${numfiles},${cpuspertask},${mem},${threads},${timelimit},${qos},${constraints},${workdir},\" >> '+f'{self.jobs_completed_file}\n'
            )

    def _validate_config(self) -> bool:
        valid = super()._validate_config()
        if not any(d.get('name', "") == 'xml' for d in self.Config["extra"]) or not any(d.get('name', "") == 'fasta' for d in self.Config["extra"]):
            valid=False
        if not self.Config["jobs"]["tool_type"]=="MQ":
            valid=False
        return valid

    """
    Method specific to MQ only, to update XML file
    """   
    def __update_xml(self,runID:str,parameters:dict) -> None:
        xml_path=next(item['path'] for item in self.Config["extra"] if item["name"] == "xml")
        if not os.path.exists(xml_path):
            logging.fatal(f"No xml file found.")
            exit()
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
                        filepath_tag.text=linuxpath
                        numfiles=numfiles+1
                    else:
                        root.findall('filePaths')[0].remove(filepath_tag)
            
            winfastapath=root.findall('fastaFiles/FastaFileInfo/fastaFilePath')[0].text
            if winfastapath != None:
                linuxfastapath=os.path.join(os.path.abspath(os.getcwd()),winfastapath.split("\\")[-1])
            
                if(os.path.exists(linuxfastapath)):
                        root.findall('fastaFiles/FastaFileInfo/fastaFilePath')[0].text=linuxfastapath
            
            #<useDotNetCore>True</useDotNetCore>
            root.findall('useDotNetCore')[0].text="True"
            #<numThreads>8</numThreads>
            numthreads=parameters["threads"]
            numthreads = numfiles if (numfiles != 0) and (numthreads==0) else numthreads
            root.findall('numThreads')[0].text=str(numthreads)
            logging.info(f"Saving new xml file : {outputfile}")
            tree.write(outputfile)

class InvalidConfigObject(Exception):
    "Raised when config object is not valid, or have missing fields"
    def __init__(self, message="Config object or Job parameters object is not valid, or have missing fields. See logs in ~/.toolparametriser/"):
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
        self.tmplfile="DiaNNtemplate.tmpl"
        self.inputfiles=[]

    def _validate_config(self) -> bool:
        valid = super()._validate_config()
        if not self.Config["jobs"]["tool_type"]=="DiaNN":
            return False
        if self.Config["jobs"]["run_type"]=="lib":
            if not any(d.get('name', "") == 'tsv' for d in self.Config["extra"]) or not any(d.get('name', "") == 'fasta' for d in self.Config["extra"]):
                return False
        elif not any(d.get('name', "") == 'fasta' for d in self.Config["extra"]):
                return False
        if not self.Config["jobs"]["tool_type"]=="DiaNN":
            valid=False
        return valid

    def _run_job(self,runID,parameters,work_dir):
        parameters['inputfiles']=' --f '.join(self.__get_input_files(runID=runID))
        super()._run_job(runID=runID,parameters=parameters,work_dir=work_dir)

    def _create_jobscript_template(self,**kwargs):

        with open(os.path.join(self.Config["Output_path"],self.tmplfile), "w+") as fb:
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
            fb.writelines("#SBATCH --qos=${qos}\n")
            fb.writelines("#SBATCH --constraint=${constraints}\n")
            fb.writelines("module use /stornext/System/data/modulefiles/sysbio\n")
            fb.writelines("module load DiaNN/1.8\n")
            fb.writelines("diann-1.8 ")
            fb.writelines(" --f ${inputfiles} --lib \"${lib}\"")
            fb.writelines("--threads ${threads} --verbose 4 ")
            fb.writelines(" --fasta \"${fastafile}\" ")
            fb.writelines(" ${args} \n")
            
            fb.writelines(
                'echo \"${jobtype},$SLURM_JOB_ID,${partition},${numfiles},${cpuspertask},${mem},${threads},${timelimit},${qos},${constraints},${workingdir},type=${type}\" >> '+f'{self.jobs_completed_file}\n'
            )
    """ 
    Method specific to Diann only
    """  
    def __get_input_files(self,runID:str)->list:
        outpath=os.path.join(self.Config["Output_path"],runID,self.Config["input"]["ext"])
        return glob.glob(outpath, recursive=False)

    '''Overriding get_tmpl_values to add input files'''   
    def _get_tmpl_values(self,parameters:dict,work_dir:str)->dict:
        params=super()._get_tmpl_values(parameters=parameters,work_dir=work_dir)
        if 'inputfiles'  in parameters.keys():
            params['inputfiles']=parameters['inputfiles']

        params['type']=self.Config["jobs"]["run_type"]
        if params['type']=="lib":
            params['lib']=next(item['path'] for item in self.Config["extra"] if item["name"] == "tsv")
            params["args"]="".join([
            " --out \"./outputreport.tsv\" ",
            " --qvalue 0.01 --matrices  --out-lib \"./spectrallib.tsv\" ",
            " --gen-spec-lib --predictor --met-excision --cut \"K*,R*\" --mass-acc 10 --mass-acc-ms1 10.0 --use-quant --reanalyse",
            
            " --smart-profiling --peak-center --no-ifs-removal \n"])
            
        elif params['type']=="libfree":
            params['lib']=""
            params["args"]="".join([
            " --out \"./outputreport.tsv\" ",
            " --qvalue 0.01 --matrices  --out-lib \"./spectrallib.tsv\" --gen-spec-lib --predictor --fasta-search  ",
            " --min-fr-mz 200 --max-fr-mz 1800 --met-excision --use-quant  ",
            " --cut \"K*,R*\" --missed-cleavages 1 --min-pep-len 7 --max-pep-len 30 --min-pr-mz 300  ",
            " --max-pr-mz 1800 --min-pr-charge 1 --max-pr-charge 4 --mass-acc 10 --mass-acc-ms1 10.0  ",
            " --reanalyse --smart-profiling --peak-center --no-ifs-removal"])

        params['fastafile']=next(item['path'] for item in self.Config["extra"] if item["name"] == "fasta")
        return params

class FromCMDTester(AbstractTester):
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.tmplfile="Generictemplate.tmpl"
    def  _create_jobscript_template(self,**kwargs):
        tmplpath = os.path.join(self.Config["Output_path"],self.tmplfile)
        logging.info("Writing sbatch job template to {p}.".format(p=tmplpath))
        with open(tmplpath, "w+") as fb:
            fb.writelines("#!/bin/bash\n")
            fb.writelines("#SBATCH -p ${partition}\n")
            fb.writelines("#SBATCH --job-name=${jobname}\n")
            fb.writelines("#SBATCH --ntasks=${ntasks}\n")
            fb.writelines("#SBATCH --time=${timelimit}\n")
            fb.writelines("#SBATCH --cpus-per-task=${cpuspertask}\n")
            fb.writelines("#SBATCH --mem=${mem}G\n")
            fb.writelines("#SBATCH --gres=${gres}\n")
            fb.writelines("#SBATCH --output=slurm-%j.out\n")
            fb.writelines("#SBATCH --mail-type=ALL,ARRAY_TASKS\n")
            fb.writelines("#SBATCH --mail-user=${email}\n")
            fb.writelines("#SBATCH --qos=${qos}\n")
            fb.writelines("#SBATCH --constraint=${constraints}\n")

            fb.writelines("${modules}\n")
            if 'cmd' in self.Config["jobs"]:
                fb.writelines(f"{self.Config['jobs']['cmd']}\n")
            
            fb.writelines(
                'echo \"${jobtype},$SLURM_JOB_ID,${partition},${numfiles},${cpuspertask},${mem},${threads},${timelimit},${qos},${constraints},${workingdir},type=${type}\" >> '+f'{self.jobs_completed_file}\n'
            )
        logging.debug("Successfully wrote sbatch job templte, {p}.".format(p=tmplpath))
    
    def _run_job(self,runID,parameters,work_dir):
        
        super()._run_job(runID=runID,parameters=parameters,work_dir=work_dir)

    def _get_modules(self):
        modules_str=""
        if "modules" in self.Config:
            for mod in self.Config["modules"]:
                if "use" in mod:
                    modules_str+=f"module use {mod['use']}\n"
                if "name" in mod:
                    modules_str+=f"module load {mod['name']}\n"
        return modules_str

    '''Overriding get_tmpl_values'''   
    def _get_tmpl_values(self,parameters:dict,work_dir:str)->dict:
        params=super()._get_tmpl_values(parameters=parameters,work_dir=work_dir)
        params["modules"]=self._get_modules()
        if "cmd_placeholder" in self.Config:
            for placeholder in self.Config["cmd_placeholder"]:
                if "name" in placeholder and "path" in placeholder:
                    params[placeholder["name"]]=placeholder["path"]
        return params    
    