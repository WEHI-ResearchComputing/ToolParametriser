# Tool Parameteriser
A tool to make benchmarking and parameterising HPC tools easier and streamlined.

When running a new tool on a HPC, researchers find it challenging to chose the resources required for the job and also how the resources scale with the size of the input dataset. This tool helps researchers answer these kind of questions and also helps Research Computing teams recommed best combination of resources for specific tool.

## Install
**Requires Python 3.11**
```
pip install git+ssh://git@github.com/WEHI-ResearchComputing/ToolParametriser.git
```

Example configuration files are located in the [examples](https://github.com/WEHI-ResearchComputing/ToolParametriser/tree/main/examples) directory of this repo.

## To run a test
```
toolparameteriser -c <configfile> -R run
```
Test config file examples are found in `examples`
* MQ `configMQ.toml`
* Diann `configDiaNN_lib.toml` and `configDiaNN_libfree.toml`
* bwa `configBWA.toml`
* ONT guppy `configONTGuppy.toml`
* ONT guppy "real" parameter run-time parameter scan `configONTGuppy-fullscan.toml`

## To collect test results

Another config file needs to be created with the `[output]` table and the `jobs_details_path` and `results_file` keys. For example, `configAnalysis.toml` in [the examples directory](https://github.com/WEHI-ResearchComputing/ToolParametriser/blob/main/examples/configAnalysis.toml):
```
[output]
jobs_details_path = "/vast/scratch/users/iskander.j/test2/jobs_dev.csv" 
results_file="/vast/scratch/users/iskander.j/test2/devresults.csv"
```
* `jobs_details_path` should be pointed to the `jobs_completed.csv` file that can be found in the `path` key in the `[output]` table of the run config file.
* `results_file` is the file in which to place the parsed output. This will be in CSV format.

Collect the results with
```
toolparameteriser -c <configfile> -R analyse
```
The reuslts file will be a CSV file where each row corresponds to a job found in the `jobs_detail_path` CSV file. It will add CPU and memory effeciency data, and elapsed wall time retrieved from the `seff` command along with other periferal information about the job. For example:
```
JobId,JobType,NumFiles,Threads,Extra,Nodes,CPUs Requested,CPUs Used,CPUs Efficiency,Memory Requested,Memory Used,Memory Efficiency,GPUs Used,Time,WorkingDir,Cluster,Constraints
10829380,diamondblast_32t,1,32,type=,1,32,24.32,76.63,200.0,151.04,75.52,0,2000,nan,milton,Broadwell
10829375,diamondblast_32t,1,32,type=,1,32,22.4,70.87,200.0,77.36,38.68,0,2151,nan,milton,Broadwell
10829381,diamondblast_32t,1,32,type=,1,32,22.4,70.79,200.0,169.1,84.55,0,2171,nan,milton,Broadwell
...
```

## How it works
The user have two prepare two files
* Configuration (Config) File

    This is used to setup all parameters needed to setup and run the test
* Jobs Parameters File

    This is a csv file, used to specify slurm job parameters to run. Each row defines parameters to a job.
    
Such that each test will run a number of slurm jobs each with parameters specifies in the `Jobs Parameters File`.

When the test starts, the test output directory is created and for each job the following happens:
1. Job directory created
2. If input files are specified they will be copied to the job directory
3. Submission script will be created from a template that will include the cmd specified in the config file. The template is saved into the test output directory.
4. The job is submitted to SLURM using the job directory as the working directory.

## Preparing Config File
Config files are TOML files. Each config file describes parameters that are the same across all jobs. Example config file are found in `examples`
* MQ `configMQ.toml`
* Diann `configDiaNN_lib.toml` and `configDiaNN_libfree.toml`
* bwa `configBWA.toml`
* For collecting of results use `configAnalysis.toml`

### For running test, the following sections can be specified

* **input**

Sets where the pool of input files are located (`path` key) and type of input files whether dir or file (`type` key). If `[input]` is provided, the path directory/file will be copied to each job's working directory.

```
[input]
type="dir"
path = "<full path>"
```

* **List of modules**

A non-compulsory list of modules and each have use and name fields. use is optional if the required module is visible by default.
```
[[modules]]
use="/stornext/System/data/modulefiles/bioinf/its"
name="bwa/0.7.17"
[[modules]]
name="gatk/4.2.5.0"
```

* **output**

Sets where the output files will be saved. All files related to the tests will be placed in this directory.
```
[output]
path = "<full output dir path>" 
```

* **jobs**

To set fields related to the slurm jobs to be submitted. The fields include
* `cmd`: the command to run for each test. Placeholders can be included with `${}`. Compulsory.
* `num_reps`: the number of repetitions execute each job. Compulsory.
* `params_path`: the path to the jobs profile CSV file. Compulsory.
* `tool_type`: the tool being tested. This is used to name the job folders. Compulsory (can be supplied an empty string i.e., "").
* `run_type`: the type of run being tested. This is used to name the job folders. Compulsory (can be supplied an emptry string i.e., "").

The following are parameters supplied to Slurm and must be included in either the config file or the jobs profile file. If included in both, the values in the jobs profile CSV file take precedence. To use the default values, supply an empty string i.e., "".
* `email`: the email to send Slurm job start/end notifications to.
* `qos`: the QoS to run jobs under.
* `partition`: the partition to run jobs in.
* `timelimit`: the max wall time to run each job with.
* `cpuspertask`: the number of CPUs per task to run each job with.
* `mem`: the memory (in GB) to run each job with.
* `gres`: the number of "general resources" to request. A 0 value must be supplied if not needed. e.g., `gres = "gpu:0"` must be specified if no GPUs are needed.
* `constraint`: any constraints e.g., for Milton HPC, you can specify the microarchitecture with `constraint = "Skylake"`.

Using the `configBWA.toml` example found in the `examples` folder:
```
[jobs]
cmd="bwa mem -t ${threads} -K 10000000 -R '@RG\\tID:sample_rg1\\tLB:lib1\\tPL:bar\\tSM:sample\\tPU:sample_rg1' ${reference} ${input_path} | gatk SortSam --java-options -Xmx30g --MAX_RECORDS_IN_RAM 250000 -I /dev/stdin -O out.bam --SORT_ORDER coordinate"
num_reps = 1 
params_path = "/vast/scratch/users/yang.e/ToolParametriser/examples/IGenricbenchmarking-profiles.csv" 
tool_type="bwa"
run_type=""
email=""
qos="preempt"
```

* **List of command placeholders**

A list of command placeholders and each have name and path fields. These are placeholders that are defined in the cmd field defined inside jobs.
```
[[cmd_placeholder]]
name="reference"
path="/vast/projects/RCP/23-02-new-nodes-testing/bwa-gatk/bwa-test-files/Homo_sapiens_assembly38.fasta"
[[cmd_placeholder]]
name="input_path"
path="samples/*"
```

## Preparing Jobs Profile
The jobs' profiles are stored in a CSV file, and must be linked to in the config file under the `[job]` table and `params_path` key:
```
[jobs]
params_path="/path/to/jobsprofile.csv"
```
Column headers in the jobs profile CSV file correspond to job Slurm parameters or command placeholders. If a column exists in both the jobs profile CSV and the config TOML file, then the former takes precedence. An example of this scenario is in `examples/configBWA2.toml` and `examples/BWA-profile2.csv`.
