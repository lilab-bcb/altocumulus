import argparse
from pathlib import Path

import fsspec
import pandas as pd
import matplotlib.pyplot as plt
from dateutil.parser import parse

from alto.utils.io_utils import _get_scheme


def main(argv):
    parser = argparse.ArgumentParser(
        description="Output report containing CPU, memory, and disk usage from monitoring log file"
    )
    parser.add_argument(
        dest="path",
        help="Path to monitoring log file or path to a directory to search for monitoring.log files",
    )
    parser.add_argument(
        dest="report",
        help="Report file output path",
    )
    parser.add_argument(
        "--plot",
        dest="plot",
        action="store",
        required=False,
        help="Optional filename to create a plot of utilization vs. time for each task",
    )
    args = parser.parse_args(argv)
    execute(args.path, args.report, args.plot)


def execute(input_path, report_filename, plot_filename=None):
    generate_plot = plot_filename is not None
    if generate_plot:
        from pandas.plotting import register_matplotlib_converters

        register_matplotlib_converters()
    scheme = _get_scheme(input_path)
    fs = fsspec.filesystem(scheme)

    is_dir = fs.isdir(input_path)
    if is_dir:
        input_path = input_path.rstrip(fs.sep)
        log_paths = fs.glob(input_path + f"{fs.sep}**{fs.sep}monitoring.log", recursive=True)
        if len(log_paths) == 0:
            raise ValueError("No monitoring.log files found")
    else:
        log_paths = [input_path]

    if generate_plot:
        ncol = 1
        nrow = len(log_paths)
        fig, axes = plt.subplots(
            nrow, ncol, squeeze=True, sharex=False, sharey=False, figsize=(8, nrow * 4)
        )
    results = []
    for i in range(len(log_paths)):
        log_path = log_paths[i]
        task, shard = get_task_and_shard(log_path) if is_dir else None
        result = parse_log(
            scheme + "://" + log_path,
            details=generate_plot,
        )
        if task is not None:
            result["task"] = task
            result["shard"] = shard

        if generate_plot:
            ax = axes[i]
            plot_single_task(result, ax)
        del result["details"]

        results.append(result)
    pd.DataFrame(results).to_csv(report_filename, sep="\t", index=False)
    if generate_plot:
        fig.tight_layout()
        fig.savefig(plot_filename)


def _figsize(nrow=1, ncol=1, aspect=1, size=3):
    return ncol * size * aspect, nrow * size


def get_task_and_shard(log_path):
    p = Path(log_path)
    shard_name = p.parent.name
    if shard_name == "cacheCopy" or shard_name.startswith("attempt-"):
        p = p.parent
        shard_name = p.parent.name

    if shard_name.startswith("shard-"):
        task_name = p.parent.parent.name

    else:
        task_name = shard_name
        shard_name = ""

    if task_name.startswith("call-"):
        task_name = task_name[len("call-") :]
    # gs://output/cromwell_execution/xxx_workflow/92f48dc5-6/call-xxx_task/shard-0/monitoring.log
    # gs://output/cromwell_execution/xxx_workflow/92f48dc5-6/call-xxx_task/shard-0/cacheCopy/monitoring.log
    return task_name, shard_name


def parse_log(path, details=True) -> dict:
    max_memory_percent = 0
    max_cpu_percent = 0
    max_disk_percent = 0

    cpus = None
    total_memory = None
    total_disk = None
    elapsed_minutes = 0

    # details
    times = []
    cpu_values = []
    memory_values = []
    disk_values = []

    with fsspec.open(path, "rt") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                # e.g. [Tue Jan 24 17:34:29 UTC 2023]
                times.append(parse(line[1:-1]))
            if line.startswith("* CPU usage:"):
                value = float(line[line.index(":") + 1 : len(line) - 1])
                if details:
                    cpu_values.append(value)
                max_cpu_percent = max(max_cpu_percent, value)
            elif line.startswith("* Memory usage:"):
                value = float(line[line.index(":") + 1 : len(line) - 1])
                if details:
                    memory_values.append(value)
                max_memory_percent = max(max_memory_percent, value)
            elif line.startswith("* Disk usage:"):
                value = float(line[line.index(":") + 1 : len(line) - 1])
                if details:
                    disk_values.append(value)
                max_disk_percent = max(max_disk_percent, value)
            elif line.startswith("#CPU"):
                cpus = int(line[line.index(":") + 1 : len(line)])
            elif line.startswith("Total Memory:"):
                total_memory = float(line[line.index(":") + 1 : len(line) - 1])
            elif line.startswith("Total Disk space:"):
                total_disk = float(line[line.index(":") + 1 : len(line) - 1])
    if len(times) >= 2:
        elapsed_minutes = ((times[-1] - times[0]).total_seconds()) / 60

    return dict(
        max_memory_percent=max_memory_percent,
        max_cpu_percent=max_cpu_percent,
        max_disk_percent=max_disk_percent,
        cpus=cpus,
        total_memory=total_memory,
        total_disk=total_disk,
        elapsed_minutes=elapsed_minutes,
        details=dict(times=times, cpu=cpu_values, memory=memory_values, disk=disk_values),
    )


def plot_single_task(result, ax):
    cpu_str = "{:.0f}/{} ({:.0f}%)".format(
        result["max_cpu_percent"] / 100 * result["cpus"], result["cpus"], result["max_cpu_percent"]
    )
    memory_str = "{:.1f}/{:.1f} ({:.0f}%)".format(
        result["max_memory_percent"] / 100 * result["total_memory"],
        result["total_memory"],
        result["max_memory_percent"],
    )
    disk_str = "{:.0f}/{:.0f} ({:.0f}%)".format(
        result["max_disk_percent"] / 100 * result["total_disk"],
        result["total_disk"],
        result["max_disk_percent"],
    )
    details = result["details"]
    times = details["times"]
    # convert times to elapsed times in minutes
    if len(times) >= 2:
        start_time = times[0]
        new_times = []
        for i in range(len(times)):
            delta = times[i] - start_time
            new_times.append(delta.total_seconds() / 60.0)

        times = new_times
        task_name = result.get("task")
        shard = result.get("shard")
        if task_name is not None:
            title = task_name
            if shard is not None:
                title = f"{title} ({shard})"
            ax.set_title(title)
        cpu_values = details["cpu"]
        memory_values = details["memory"]
        disk_values = details["disk"]
        ax.plot(times, cpu_values, label="CPU, " + cpu_str)
        ax.plot(times, memory_values, label="Memory, " + memory_str)
        ax.plot(times, disk_values, label="Disk, " + disk_str)
        ax.set_ylim([0, 100])
        ax.set_xlabel("Elapsed Minutes")
        ax.set_ylabel("Percent")
        ax.legend()

    else:
        print("Not enough values to plot")
