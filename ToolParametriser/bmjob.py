class Job(ABC):
    """
    The Job interface declares the operations that all concrete jobs
    must implement.
    """

    @abstractmethod
    def readBenchmarkingProfiles(self) -> list:
        pass

    @abstractmethod
    def createRepository(self) -> None:
        pass

    @abstractmethod
    def copyInputFiles(self) -> None:
        pass

    @abstractmethod
    def copySpecificInputFiles(self) -> None:
        pass

    @abstractmethod
    def createExecutableBatchFile(self) -> str:
        pass

    @abstractmethod
    def identifySpecificInputFiles(self) -> None:
        pass


"""
Concrete Jobs provide various implementations of the Job interface.
"""
class AbstractJob(Job):
    def __init__(
        self,
        BenchmarkingCSVFile_path,
        InputFiles_path,
        storage_path,
        Number_of_jobs_repetition,
    ):
        self.csvfile = BenchmarkingCSVFile_path
        self.path = InputFiles_path
        self.src = storage_path
        self.dest = Number_of_jobs_repetition

    def readBenchmarkingProfiles(self) -> list:
        job_parameters = []

        with open(self.csvfile, "r") as file:
            csv_file = csv.DictReader(file)
            for row in csv_file:
                job_parameters.append(dict(row))

        return job_parameters

    def createRepository(self,running_job_path) -> None:
        os.makedirs(running_job_path)

    def copyInputFiles(self, src, dest) -> None:
        try:
            shutil.copytree(src, dest, dirs_exist_ok=True)
        except NotADirectoryError:
            shutil.copy(src, dest)

    def copySpecificInputFiles(self) -> str:
        return "{Result of the AbstractJob: copySpecificInputFiles}"

    def createExecutableBatchFile(self) -> str:
        return "{Result of the AbstractJob: createExecutableBatchFile}"

    def identifySpecificInputFiles(self) -> str:
        return "{Result of the AbstractJob: identifySpecificInputFiles}"


class MaxQuantJob(AbstractJob):
    def __init__(
        self,
        BenchmarkingCSVFile_path,
        InputFiles_path,
        storage_path,
        Number_of_jobs_repetition,

    ):
        super().__init__(
            BenchmarkingCSVFile_path,
            InputFiles_path,
            storage_path,
            Number_of_jobs_repetition,
        )
        # TODO: Variables needs to be initialize 
        # self.sample_files = sample_files
        # self.xml_file_path = xml_file_path
        # self.numthreads = numthreads

    def createExecutableBatchFile(self, job_parameters, path, ExecutionID) -> None:
        with open(f"{path}{job_parameters['job-name']}_batch.sh", "w+") as fb:
            fb.writelines("#!/bin/bash\n")
            fb.writelines(f"#SBATCH -p {job_parameters['partition']}\n")
            fb.writelines(f"#SBATCH --qos=regular_partitiontimelimit\n")
            fb.writelines(f"#SBATCH --job-name={job_parameters['job-name']}\n")
            fb.writelines(f"#SBATCH --ntasks=1\n")
            fb.writelines(f"#SBATCH --time={job_parameters['timelimit']}\n")
            fb.writelines(
                f"#SBATCH --cpus-per-task={job_parameters['cpus-per-task']}\n"
            )
            fb.writelines(f"#SBATCH --mem={job_parameters['mem']}G\n")
            fb.writelines(f"#SBATCH --output={path}slurm-%j.out\n")
            fb.writelines(f"#SBATCH --mail-type=ALL,ARRAY_TASKS\n")
            fb.writelines(f"#SBATCH --mail-user=bollands.c@wehi.edu.au\n")

            fb.writelines(f"module load MaxQuant/2.0.2.0\n")
            fb.writelines(f"module load python/3.8.8\n")

            fb.writelines(
                f"MaxQuant {path}mqpar.xml --changeFolder {path}mqpar.post.xml {path} {path}\n"
            )

            fb.writelines(f"MaxQuant {path}mqpar.post.xml\n")

            fb.writelines(
                f"find {path} -maxdepth 1 -mindepth 1 -type f -not -regex '.*\.\(fasta\|xml\|out\|raw\|sh\)' -delete\n"
            )
            fb.writelines(
                f"find {path} -maxdepth 1 -mindepth 1 -type d -not -regex '.*\.\(d\)' -exec rm -rf '{{}}' \;\n"
            )

            fb.writelines(
                f'echo ""$SLURM_ARRAY_JOB_ID","$SLURM_ARRAY_TASK_ID"",{job_parameters["partition"]},{job_parameters["type"]},{job_parameters["job-name"]},{job_parameters["NumFiles"]},{job_parameters["cpus-per-task"]},{job_parameters["mem"]},{job_parameters["threads"]},{job_parameters["timelimit"]} >> jobs_executed_{ExecutionID}.txt\n'
            )

        os.system(f"sbatch {path}{job_parameters['job-name']}_batch.sh")

    def updateXmlFile(self, sample_files, xml_file_path, numthreads) -> None:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        for filepath_tag in root.findall("filePaths/string"):
            root.findall("filePaths")[0].remove(filepath_tag)

        for sample_file in sample_files:
            new_path = ET.Element("string")
            new_path.text = sample_file
            root.findall("filePaths")[0].append(new_path)

        # <useDotNetCore>True</useDotNetCore>
        root.findall("useDotNetCore")[0].text = "True"
        # <numThreads>8</numThreads>
        root.findall("numThreads")[0].text = str(numthreads)

        outputfile = xml_file_path
        tree.write(outputfile)


class DiaNNJob(AbstractJob):
   
    def __init__(
        self,
        BenchmarkingCSVFile_path,
        InputFiles_path,
        storage_path,
        Number_of_jobs_repetition,
    ):
        super().__init__(
            BenchmarkingCSVFile_path,
            InputFiles_path,
            storage_path,
            Number_of_jobs_repetition,
        )
    
    def identifySpecificInputFiles(self) -> dict:
        print("in DiaNNJob indenfiyspecificinpoutfiles")
        # Extract the list of Input filenames: .Fasta, .tsv and .d
        original_files = glob.glob(os.path.join(self.path, "*.d"), recursive=False)
        
#         print(self.path)

        # Create a Dictionary to store Input Files Orderly
        DiaNNSpecificInputFiles = {}
        DiaNNSpecificInputFiles["original_files"] = original_files
        DiaNNSpecificInputFiles["fasta_file"] = glob.glob(os.path.join(self.path, "*.fasta"), recursive=False
        )[0]
        

        if glob.glob(os.path.join(self.path, "*.tsv"), recursive=False):
            DiaNNSpecificInputFiles["tsv_file"] = glob.glob(os.path.join(self.path, "*.tsv"), recursive=False)[0]
        else:
            DiaNNSpecificInputFiles["tsv_file"] = None
            
        return DiaNNSpecificInputFiles

    def copySpecificInputFiles(self,specificInputFiles, running_job_path) -> None:
        print("in DiaNNJob coptspecificinputfuiles")
        # Copy Fasta & XML File
        self.copyInputFiles(specificInputFiles["fasta_file"], running_job_path)
                
        if specificInputFiles["tsv_file"]:
            self.copyInputFiles(specificInputFiles["tsv_file"], running_job_path)

    def createExecutableBatchFile(
        self, job_parameters, path, specificInputFiles, ExecutionID
    ) -> None:
        print("in DiaNNJob createexecutablebatchfile")
        os.system(f'(cd {path} ; DIANN_RUN_TYPE=""{job_parameters["type"]}"" DIANN_LIB=""{specificInputFiles["tsv_file"]}"" DIANN_TIME=""{job_parameters["timelimit"]}""  DIANN_CPUS=""{job_parameters["cpus-per-task"]}"" DIANN_MEM=""{job_parameters["mem"]}G"" DIANN_THREADS=""{job_parameters["threads"]} DIANN_OUTPUT_PATH=""{path}/output"" /stornext/System/data/apps/rc-tools/rc-tools-1.0/bin/tools/DiaNN/createdianncmd.sh)')

        with open(f"{path}diann.slurm", "a") as fb:
            fb.writelines(f'echo ""$SLURM_JOB_ID"",{job_parameters["partition"]},{job_parameters["type"]},{job_parameters["job-name"]},{job_parameters["NumFiles"]},{job_parameters["cpus-per-task"]},{job_parameters["mem"]},{job_parameters["threads"]},{job_parameters["timelimit"]} >> jobs_executed_{ExecutionID}.txt\n')

        os.system(f"sbatch {path}diann.slurm")
class GenericJob(AbstractJob):
    
    def __init__(
        self,
        BenchmarkingCSVFile_path,
        InputFiles_path,
        storage_path,
        Number_of_jobs_repetition,
    ):
        super().__init__(
            BenchmarkingCSVFile_path,
            InputFiles_path,
            storage_path,
            Number_of_jobs_repetition,
        )
        
    def identifySpecificInputFiles(self) -> dict:
#         files_in_script = int(input("Do you have the files for your script, 1 = yes, 2 = no"))
#         if files_in_script == 1:
#             print("1")
#             #basically just run script i think
#         if files_in_script == 2:
#             print("2")
            file_type = input("What is the extension of the file you are trying to benchmark with? eg. .bam WITH THE '.' AT THE START")
            original_files = glob.glob(os.path.join(self.path, f"*{file_type}"), recursive=False)
            print(original_files)
        
#             print(self.path)

            # Create a Dictionary to store Input Files Orderly
            GenreicInputFiles = {}
            GenreicInputFiles["original_files"] = original_files
            GenreicInputFiles["fasta_file"] = glob.glob(os.path.join(self.path, f"*{file_type}"), recursive=False
            )[0]


            if glob.glob(os.path.join(self.path, "*.tsv"), recursive=False):
                GenreicInputFiles["tsv_file"] = glob.glob(os.path.join(self.path, "*.tsv"), recursive=False)[0]
            else:
                GenreicInputFiles["tsv_file"] = None

            return GenreicInputFiles
                #find the files and add them to the script anyway
    def copySpecificInputFiles(self,specificInputFiles, running_job_path) -> None:
        # Copy Fasta & XML File
        self.copyInputFiles(specificInputFiles["fasta_file"], running_job_path)
                
        if specificInputFiles["tsv_file"]:
            self.copyInputFiles(specificInputFiles["tsv_file"], running_job_path)

    def createExecutableBatchFile(
        self, job_parameters, path, specificInputFiles, ExecutionID, 
    ) -> None:
#         print("in DiaNNJob createexecutablebatchfile")
        os.system(f'({path}')

        with open(f"{path}generic.slurm", "a") as fb:
            fb.writelines(f'echo ""$SLURM_JOB_ID"",{job_parameters["partition"]},{job_parameters["type"]},{job_parameters["job-name"]},{job_parameters["NumFiles"]},{job_parameters["cpus-per-task"]},{job_parameters["mem"]},{job_parameters["threads"]},{job_parameters["timelimit"]} >> jobs_executed_{ExecutionID}.txt\n')

#         os.system(f"sbatch {path}diann.slurm")

