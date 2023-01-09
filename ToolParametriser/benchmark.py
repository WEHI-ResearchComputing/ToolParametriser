from abc import ABC, abstractmethod
from datetime import datetime
import random,os 
import bmjob

class BenchmarkCreator(ABC):
    """
    The BenchmarkingToolCreator class declares the factory method that is supposed to return an
    object of a Job class. The BenchmarkingToolCreator's subclasses usually provide the
    implementation of this method.
    """

    def __init__(
        self,
        BenchmarkingCSVFile_path,
        InputFiles_path,
        storage_path,
        Number_of_jobs_repetition,
    ):
        self.BenchmarkingCSVFile_path = BenchmarkingCSVFile_path
        self.InputFiles_path = InputFiles_path
        self.storage_path = storage_path
        self.Number_of_jobs_repetition = Number_of_jobs_repetition

    @abstractmethod
    def factory_method_create_job(self):
        """
        Note that the BenchmarkingToolCreator may also provide some default implementation of
        the factory method.
        """
        pass

    def runBenchmarking(self) -> str:
        print("benchmarkingtoolcreator runBenchmarking")
        
        """
        Also note that, despite its name, the BenchmarkingToolCreator's primary responsibility
        is not creating jobs. Usually, it contains some core business logic
        that relies on Job objects, returned by the factory method.
        Subclasses can indirectly change that business logic by overriding the
        factory method and returning a different type of job from it.
        """

        # Call the factory method to create a Job object.
        job = self.factory_method_create_job()
        # Now, use the job.

        # TODO: Inside of this method will be our core business logic
        
        # current date and time
        now = datetime.now()

        # ID to identify each Benchmarking executed
        ExecutionID = now.strftime("%Y%m%d%H%M%S")

        # Storing job_parameters of CSV file
        job_parameters = job.readBenchmarkingProfiles()

        # Specific files Identification (.tsv, .d, .xml, .fasta)
        specificInputFiles = job.identifySpecificInputFiles()

        # Let's run the job according to the number of repetition
        for parameters in job_parameters:

            for _ in range(0, self.Number_of_jobs_repetition):
                now = datetime.now()  # current date and time
                JobExecutionID = now.strftime("%Y%m%d%H%M%S")
                running_job_path = os.path.join(self.storage_path,f"repo-{parameters['job-name']}-{JobExecutionID}/")

                job.createRepository(running_job_path)

                # Copy samples files k = number of input files to randomly select
                sample_files = random.sample(specificInputFiles["original_files"], k=int(parameters["NumFiles"]))
                specificInputFiles["sample_files"] = sample_files

                for sample_file_path in specificInputFiles["sample_files"]:
                    name_of_folder = sample_file_path.split("/")[-1]
                    job.copyInputFiles(sample_file_path, os.path.join(running_job_path , name_of_folder))

                # Copy ONLY specific input files such (.tsv, .xml, .fasta)
                job.copySpecificInputFiles(specificInputFiles, running_job_path)
        
                # Create and Execute the SBatch File

                job.createExecutableBatchFile(
                    parameters,
                    running_job_path,
                    ExecutionID,specificInputFiles=specificInputFiles
                )

        
        # result = f"BenchmarkingToolCreator: The same creator's code has just worked with {job.readBenchmarkingProfiles()}"
        result = "BenchMe has finished running"

        return result
"""
Concrete Creators override the factory method in order to change the resulting
product's type.
"""

class MQBenchmarkingTool(BenchmarkCreator):
    """
    Note that the signature of the method still uses the abstract job type,
    even though the concrete job is actually returned from the method. This
    way the BenchmarkingToolCreator can stay independent of concrete job classes.
    """
    def __init__(self,BenchmarkingCSVFile_path, InputFiles_path, storage_path, Number_of_jobs_repetition,):
        super().__init__(BenchmarkingCSVFile_path, InputFiles_path, storage_path, Number_of_jobs_repetition)

        # TODO: Variables needs to be initialize
        # Extract the list of Input filenames: .Fasta, .XML and .d
        # original_files = glob.glob(InputFiles_path + "*.d", recursive=False)

        # Create a Dictionary to store Input Files Orderly
        # MaxQuantInputFiles = {}
        # MaxQuantInputFiles["fasta_file"] = glob.glob(InputFiles_path + "*.fasta", recursive=False)[0]
        # MaxQuantInputFiles["xml_file"] = glob.glob(InputFiles_path + "*.xml", recursive=False)[0]

        # self.sample_files = sample_files
        # self.xml_file_path = xml_file_path
        # self.numthreads = numthreads
        
    def factory_method_create_job(self) -> bmjob.BMJob:
        return bmjob.MaxQuantJob(self.BenchmarkingCSVFile_path,self.InputFiles_path,self.storage_path,self.Number_of_jobs_repetition )


class DiaNNBenchmarkingTool(BenchmarkCreator):
    def __init__(self,BenchmarkingCSVFile_path, InputFiles_path, storage_path, Number_of_jobs_repetition):
        super().__init__(BenchmarkingCSVFile_path, InputFiles_path, storage_path, Number_of_jobs_repetition)
      
        
    def factory_method_create_job(self) -> bmjob.BMJob:
        return bmjob.DiaNNJob(self.BenchmarkingCSVFile_path,self.InputFiles_path,self.storage_path,self.Number_of_jobs_repetition)
    
class GenericBenchmarkingTool(BenchmarkCreator):
    def __init__(self,BenchmarkingCSVFile_path, InputFiles_path, storage_path, Number_of_jobs_repetition):
        super().__init__(BenchmarkingCSVFile_path, InputFiles_path, storage_path, Number_of_jobs_repetition)
        
    def factory_method_create_job(self) -> bmjob.BMJob:
        return bmjob.GenericJob(self.BenchmarkingCSVFile_path,self.InputFiles_path,self.storage_path,self.Number_of_jobs_repetition, script_dir, params)


def benchmark(creator: BenchmarkCreator) -> None:
    """
    The code works with an instance of a concrete creator, albeit through
    its base interface. As long as the client keeps working with the creator via
    the base interface, you can pass it any creator's subclass.
    """
    creator.runBenchmarking()
    
