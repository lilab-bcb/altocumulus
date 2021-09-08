import argparse
from dateutil.parser import parse



def main(argv):
    parser = argparse.ArgumentParser(description='Output maximum CPU, memory, and disk from monitoring log file')
    parser.add_argument(dest='path', help='Path to monitoring log file.')
    parser.add_argument('--plot', dest='plot', action='store', required=False, help='Optional filename to create a plot of utilization vs. time')
    args = parser.parse_args(argv)

    do_plot = args.plot is not None
    path = args.path

    if do_plot:
        import matplotlib.pyplot as plt
        from pandas.plotting import register_matplotlib_converters
        register_matplotlib_converters()

    max_memory_percent = 0
    max_cpu_percent = 0
    max_disk_percent = 0

    times = []
    cpu_values = []
    memory_values = []
    disk_values = []
    cpus = None
    cpu_str = None
    total_memory = None
    total_memory_str = None
    total_disk = None
    total_disk_str = None

    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                try:
                    times.append(parse(line[1:len(line) - 1]))
                except:
                    pass
            if line.startswith('* CPU usage:'):
                value = float(line[line.index(':') + 1:len(line) - 1])
                if do_plot:
                    cpu_values.append(value)
                max_cpu_percent = max(max_cpu_percent, value)
            elif line.startswith('* Memory usage:'):
                value = float(line[line.index(':') + 1:len(line) - 1])
                if do_plot:
                    memory_values.append(value)
                max_memory_percent = max(max_memory_percent, value)
            elif line.startswith('* Disk usage:'):
                value = float(line[line.index(':') + 1:len(line) - 1])
                if do_plot:
                    disk_values.append(value)
                max_disk_percent = max(max_disk_percent, value)
            elif line.startswith('#CPU'):
                cpus = int(line[line.index(':') + 1:len(line)])
                cpu_str = line
            elif line.startswith('Total Memory:'):
                total_memory_str = line
                total_memory = float(line[line.index(':') + 1:len(line) - 1])
            elif line.startswith('Total Disk space:'):
                total_disk_str = line
                total_disk = float(line[line.index(':') + 1:len(line) - 1])

    if do_plot:
        # convert times to elapsed times

        plt.subplot(311)
        start_time = times[0]
        new_times = []
        for i in range(len(times)):
            elapsed = ((times[i] - start_time).total_seconds()) / 60.0
            new_times.append(elapsed)

        times = new_times

        plt.plot(times, cpu_values)
        plt.suptitle(cpu_str + ', ' + total_memory_str + ', ' + total_disk_str)
        plt.ylabel('% CPU')
        plt.subplot(312)
        plt.plot(times, memory_values)

        plt.ylabel('% Memory')

        plt.subplot(313)
        plt.plot(times, disk_values)
        plt.xlabel('Elapsed Minutes')
        plt.ylabel('% Disk')

        plt.savefig(args.plot)
        
    print('Max cpu %: {}'.format(max_cpu_percent))
    print('Max memory %: {}'.format(max_memory_percent))
    print('Max disk %: {}'.format(max_disk_percent))

    print('Max cpus: {} / {}'.format(max_cpu_percent / 100 * cpus, cpus))
    print('Max memory: {} / {}'.format(max_memory_percent / 100 * total_memory, total_memory))
    print('Max disk: {} / {}'.format(max_disk_percent / 100 * total_disk, total_disk))
