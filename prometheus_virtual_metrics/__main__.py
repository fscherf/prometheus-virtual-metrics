import sys

from prometheus_virtual_metrics import handle_command_line


if __name__ == '__main__':
    handle_command_line(sys.argv[1:])
