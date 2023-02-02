
import csv
import os
import subprocess


def readExecutedJobs(executedjobs):
    with open(executedjobs, "r") as f:
        lines = f.read().splitlines()
    return lines


def checkJobOnCSV(executed_job):
    with open("benchmarking-results/final-results.csv", "a+") as f:
        reader = csv.reader(f, delimiter=",")
        for row in reader:
            if executed_job == row[1]:
                return True
        return False


def clean_data(dct):

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

    dct["Job Wall-clock time(s)"] = cpu_utilized_in_seconds

    # CPU Efficiency %
    dct["CPU Efficiency"] = dct["CPU Efficiency"].split("%")[0]

    # CPUsUsed
    dct["CPUsUsed"] = (
        int(dct["Cores per node"]) * int(float(dct["CPU Efficiency"])) / 100
    )

    # Memory Requested
    memory_efficiency_splitted = dct["Memory Efficiency"].split()

    dct["MemReq"] = memory_efficiency_splitted[2].split(".")[0]
    dct["MemUtil"] = float(memory_efficiency_splitted[0].split("%")[0])

    # Memory Used

    dct["MemUsed"] = int(dct["MemReq"]) * dct["MemUtil"] / 100

    return dct


def checkJobStatus(executed_job):

    result = subprocess.run(["seff", f"{executed_job}"], stdout=subprocess.PIPE)

    if "COMPLETED" in str(result.stdout):
        # Creates a new txt file
        with open(f"benchmarking-results/{executed_job}.txt", "w+") as f:
            subprocess.run(["seff", f"{executed_job}"], stdout=f)

        # Read the created txt
        with open(f"benchmarking-results/{executed_job}.txt", "r") as f:
            job = f.read().splitlines()

        splitted_details = []

        for detail in job:
            splitted_details.append(detail.split(": "))

        dct = {detail[0]: detail[1] for detail in splitted_details}

        dct = clean_data(dct)

        # Add the new completed job to CSV file
        with open("benchmarking-results/final-results.csv", "a") as fd:
            fd.write(
                f"{dct['Job ID']},{dct['Array Job ID']},{dct['State']},{dct['Cores per node']},{dct['CPU Utilized']},{dct['CPU Efficiency']},{dct['CPUsUsed']},{dct['Job Wall-clock time']},{dct['Job Wall-clock time(s)']},{dct['Memory Utilized']},{dct['Memory Efficiency']},{dct['MemReq']},{dct['MemUtil']},{dct['MemUsed']}\n"
            )


def main():
    executedjobs = "jobs_executed.txt"
    list_of_executed_jobs = readExecutedJobs(executedjobs)
    print(list_of_executed_jobs)

    for executed_job in list_of_executed_jobs:
        # print(f'executed job: {executed_job}')
        if checkJobOnCSV(executed_job):
            # if job is already in the CSV then continue to next iteration
            continue
        else:
            checkJobStatus(executed_job)


if __name__ == "__main__":
    main()