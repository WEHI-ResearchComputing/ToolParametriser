#!/stornext/HPCScratch/home/iskander.j/myenvs/py3_11/bin/python

import csv
import os
import subprocess
import pandas as pd
import logging,csv,math

def clean(dct):
    # Turn hours into seconds (s)
    job_wall_clock_splitted = dct["Job Wall-clock time"].replace("-", ":").split(":")
    if len(job_wall_clock_splitted) > 3:
        cpu_utilized_in_seconds = (
            (int(job_wall_clock_splitted[0]) * 24 + int(job_wall_clock_splitted[1]))
            * (60 * 60)
            + int(job_wall_clock_splitted[2]) * 60
            + int(job_wall_clock_splitted[3])
        )
    else:
        cpu_utilized_in_seconds = (
            int(job_wall_clock_splitted[0]) * 60 * 60
            + int(job_wall_clock_splitted[1]) * 60
            + int(job_wall_clock_splitted[2])
        )

    dct["time(s)"] = cpu_utilized_in_seconds

    # CPU Efficiency %
    dct["CPUEff"] = dct["CPU Efficiency"].split("%")[0]

    # CPUsUsed
    dct["CPUsUsed"] = (
        int(dct["Cores per node"])*int(dct["Nodes"]) * int(float(dct["CPUEff"])) / 100
    )
    dct["CPUsReq"] = (
        int(dct["Cores per node"])*int(dct["Nodes"])
    )
    # Memory Requested
    memory_efficiency_splitted = dct["Memory Efficiency"].split()

    dct["MemReq"] = float(memory_efficiency_splitted[2].split(" ")[0])
    dct["MemEff"] = float(memory_efficiency_splitted[0].split("%")[0])

    # Memory Used

    dct["MemUsed"] = int(dct["MemReq"]) * dct["MemEff"] / 100
    return dct


def get(completed_jobs:str,results_path,use_GPUs:bool=True):
    allresults=[]
    '''
    Input: jobtype,jobid,partition,numfiles,cpuspertask,mem,threads,timelimit,constraints,extra
    Output: JobId,Nodes,CPUs Used,CPUs Efficiency,Memory Used,Memory Efficiency,GPUs Used
    '''
    jobs=pd.read_csv(completed_jobs,index_col=False)
    #Get job ids
    #jobids=",".join(map(str,pd.read_csv(executed_jobs,header=None)[0].tolist()))
    #list_of_executed_jobs=pd.read_csv(executed_jobs,header=None)[0].tolist()
    
    for index, executed_job in jobs.iterrows():
        result = subprocess.run(["seff", f"{executed_job['jobid']}"], stdout=subprocess.PIPE)
        if result.returncode==0:
            if "COMPLETED" in str(result.stdout):
                jobdetails = result.stdout.splitlines()
                splitted_details = []
                for detail in jobdetails:
                    splitted_details.append(detail.decode("utf-8").split(": "))
                
                dct = {detail[0]: detail[1] for detail in splitted_details}
                dct = clean(dct)
                ## TODO: What if multiple Constraints?
                dct["Constraints"]=executed_job['constraints']
                dct["GPUs"]=0
                if use_GPUs:
                    result = subprocess.run(["sacct",  "-j", f"{executed_job['jobid']}", "--format=ReqTres", "--parsable", "-X","--noheader"], stdout=subprocess.PIPE)
                    
                    if result.returncode==0:
                        res=result.stdout.decode("utf-8")
                        res=res.split("|")
                        if "gres/gpu" in res[0]:
                            lines=res[0].split(",")
                            dct["GPUs"]=[x for x in lines if 'gres/gpu' in x][0].split("=")[1]
                
                if pd.isnull(executed_job["extra"]):
                    executed_job["extra"]=None
                allresults.append([executed_job["jobid"],executed_job['numfiles'],executed_job["threads"],executed_job["extra"], dct["Nodes"],dct["CPUsReq"],dct["CPUsUsed"],dct["CPUEff"],dct["MemReq"],dct["MemUsed"],dct["MemEff"],dct["GPUs"],dct["time(s)"],dct['Cluster'],dct['Constraints']])
            else:
                logging.error(f"Job {executed_job['jobid']} is still running or has failed.")

        else:
            logging.error(f"seff failed for job {executed_job['jobid']}")
    if not os.path.exists(results_path):
            with open(results_path,'w') as f:
                writer = csv.writer(f)
                writer.writerow(["JobId", "NumFiles","Threads","Extra","Nodes", "CPUs Requested","CPUs Used","CPUs Efficiency","Memory Requested","Memory Used", "Memory Efficiency","GPUs Used","Time","Cluster","Constraints"])
                writer.writerows(allresults)
    else:
        with open(results_path,'a') as f:
            writer = csv.writer(f)
            writer.writerows(allresults)