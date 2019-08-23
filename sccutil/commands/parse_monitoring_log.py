import argparse


def main(argsv):
    parser = argparse.ArgumentParser(description='Output maximum CPU, memory, and disk from monitoring.log file')
    parser.add_argument(dest='path', help='Path to monitoring.log file.', required=True)
    args = parser.parse_args(argsv)
    max_memory_percent = 0
    max_cpu_percent = 0
    max_disk_percent = 0
    path = args.path
    with open(path) as f:
        for line in f:
            line = line.strip()

            if line.startswith('* CPU usage:'):
                max_cpu_percent = max(max_cpu_percent, float(line[line.index(':') + 1:len(line) - 1]))
            elif line.startswith('* Memory usage:'):
                max_memory_percent = max(max_memory_percent, float(line[line.index(':') + 1:len(line) - 1]))
            elif line.startswith('* Disk usage:'):
                max_disk_percent = max(max_disk_percent, float(line[line.index(':') + 1:len(line) - 1]))
            elif line.startswith('#CPU'):
                cpu = int(line[line.index(':') + 1:len(line)])
            elif line.startswith('Total Memory:'):
                memory = float(line[line.index(':') + 1:len(line) - 1])
            elif line.startswith('Total Disk space:'):
                disk = float(line[line.index(':') + 1:len(line) - 1])

    print('Max cpu %: {}'.format(max_cpu_percent))
    print('Max memory %: {}'.format(max_memory_percent))
    print('Max disk %: {}'.format(max_disk_percent))

    print('Max cpus: {} / {}'.format(max_cpu_percent / 100 * cpu, cpu))
    print('Max memory: {} / {}'.format(max_memory_percent / 100 * memory, memory))
    print('Max disk: {} / {}'.format(max_disk_percent / 100 * disk, disk))
