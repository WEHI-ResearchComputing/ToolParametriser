# Tool Parametriser
A tool to make benchmarking and parametrising HPC tools easier and streamlined.

## How it works
The user have two prepare two files
* `Configuration (Config) File`

    This is used to setup all parameters needed to setup and run the test
* `Jobs Parameters File`

    This is a csv file, used to specify slurm job parameters to run. 
    
Such that each test will run a number of slurm jobs with parameters specifies in the `Jobs Parameters File`

When the test starts, test directory is created in the output path and for each job the following happens.
* Job directory created
* If input files are specified they will be copied to job directort
* Submission script will be created from a template that will include the cmd specified in the config file.
* The job is submitted to SLURM from the job directory.

## Preparing Config File
Config files are TOML files. Example config file are found in `examples`
* MQ `configMQ.toml`
* Diann `configDiaNN_lib.toml` and `configDiaNN_libfree.toml`
* bwa `configBWA.toml`
* For collecting of results use `configAnalysis.toml`

### For running test, the following sections are required

* **input**

To set where the pool of input files are located (path) and type of input files whether dir or file

```
[input]
type="dir"
path = "<full path>"
```

* **List of modules**

A list of modules and each have use and name fields. use is optional if the required module is visible by default no need to use the use field
```
[[modules]]
use="/stornext/System/data/modulefiles/bioinf/its"
name="bwa/0.7.17"
[[modules]]
name="gatk/4.2.5.0"
```

* **output**

To set where the output files will be saved
```
[output]
path = "<full output dir path>" 
```

* **jobs**

To set fields related to the slurm jobs to be submitted. The fields include
    * cmd
    * num_reps
    * params_path
    * tool_type="bwa"
    * run_type=""
    * email=""
    * qos="preempt"

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

## To run a test
```
./run.py -c <configfile> -R run
```
Test config file examples are found in `examples`
* MQ `configMQ.toml`
* Diann `configDiaNN_lib.toml` and `configDiaNN_libfree.toml`
* bwa `configbwa.toml`

## To collect test results

use a cutdown version of config such as `examples\config.toml`
```
./run.py -c <configfile> -R analyse
```

