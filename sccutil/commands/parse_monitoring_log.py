import argparse


def main(argsv):
    parser = argparse.ArgumentParser(description='Output maximum CPU, memory, and disk from monitoring log file')
    parser.add_argument(dest='path', help='Path to monitoring log file.')
    parser.add_argument('--plot', dest='plot', action='store', required=False,
        help='Optional filename to create a plot of utilization vs. time')
    args = parser.parse_args(argsv)
    do_plot = args.plot is not None

    path = args.path
    if do_plot:
        from dateutil.parser import parse
        import matplotlib.pyplot as plt
        from pandas.plotting import register_matplotlib_converters
        register_matplotlib_converters()
    max_memory_percent = 0
    max_cpu_percent = 0
    max_disk_percent = 0

    times = []
    cpu_times = []
    memory_times = []
    disk_times = []
    cpu = None
    memory = None
    disk = None
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                times.append(parse(line[1:len(line) - 1]))
            if line.startswith('* CPU usage:'):
                value = float(line[line.index(':') + 1:len(line) - 1])
                if do_plot:
                    cpu_times.append(value)
                max_cpu_percent = max(max_cpu_percent, value)
            elif line.startswith('* Memory usage:'):
                value = float(line[line.index(':') + 1:len(line) - 1])
                if do_plot:
                    memory_times.append(value)
                max_memory_percent = max(max_memory_percent, value)
            elif line.startswith('* Disk usage:'):
                value = float(line[line.index(':') + 1:len(line) - 1])
                if do_plot:
                    disk_times.append(value)
                max_disk_percent = max(max_disk_percent, value)
            elif line.startswith('#CPU'):
                cpu = int(line[line.index(':') + 1:len(line)])
            elif line.startswith('Total Memory:'):
                memory = float(line[line.index(':') + 1:len(line) - 1])
            elif line.startswith('Total Disk space:'):
                disk = float(line[line.index(':') + 1:len(line) - 1])

    if do_plot:
        plt.subplot(311)
        plt.plot_date(times, cpu_times, '-')
        plt.xlabel('Time')
        plt.ylabel('% CPU')

        plt.subplot(312)
        plt.plot_date(times, memory_times, '-')
        plt.xlabel('Time')
        plt.ylabel('% Memory')

        plt.subplot(313)
        plt.plot_date(times, disk_times, '-')
        plt.xlabel('Time')
        plt.ylabel('% Disk')

        plt.savefig(args.plot)
    print('Max cpu %: {}'.format(max_cpu_percent))
    print('Max memory %: {}'.format(max_memory_percent))
    print('Max disk %: {}'.format(max_disk_percent))

    print('Max cpus: {} / {}'.format(max_cpu_percent / 100 * cpu, cpu))
    print('Max memory: {} / {}'.format(max_memory_percent / 100 * memory, memory))
    print('Max disk: {} / {}'.format(max_disk_percent / 100 * disk, disk))
