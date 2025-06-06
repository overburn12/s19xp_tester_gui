import serial
import serial.tools.list_ports
import sys
import time
from datetime import datetime
from test_model import Test, proccess_line, print_test
from contextlib import contextmanager

class FakeSerial:
    def __init__(self, log_path):
        self.generator = replay_log_generator(log_path)
        self._has_data = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if hasattr(self.generator, 'close'):
            self.generator.close()

    @property
    def in_waiting(self):
        return int(self._has_data)  # 1 if True, 0 if False

    def readline(self):
        try:
            return next(self.generator).encode()
        except StopIteration:
            self._has_data = False
            return b''

        

def replay_log_generator(filepath):
    """
    Generator that yields log lines at the correct delay based on their timestamps.
    Lines without timestamps are yielded immediately.
    
    :param filepath: Path to the saved log file.
    :yield: Line from the log file at the appropriate replay time.
    """
    prev_timestamp = None

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                timestamp_str = line.split(']')[0].strip('[')
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                # If this line has a valid timestamp, do the sleep dance
                if prev_timestamp:
                    delta = (timestamp - prev_timestamp).total_seconds()
                    time.sleep(max(delta, 0))
                prev_timestamp = timestamp
            except (IndexError, ValueError):
                # No timestamp, or malformed — just yield it instantly
                pass

            yield line


#-----------------------------------------------------------------------------------------------------------------------
#
#-----------------------------------------------------------------------------------------------------------------------

def save_log(file_path, data):
    try:
        with open(file_path, 'a') as file:
            file.write(data + '\n')
        print("Log saved successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")


def list_com_ports():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No COM ports found.")
        sys.exit(1)
    print("Available COM ports:")
    for i, port in enumerate(ports):
        print(f"{i}: {port.device} - {port.description}")
    return ports


def select_port(ports):
    if len(ports) == 1:
        return ports[0].device
    while True:
        try:
            index = int(input("Enter the number of the COM port to use: "))
            if 0 <= index < len(ports):
                return ports[index].device
            else:
                print("Invalid number, try again.")
        except ValueError:
            print("That's not a number. Try again.")


def read_serial_forever(port_name, baudrate=115200, simulate = False, read_log = ""):
    serial_log = ""
    file_name = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

    try:
        loop_iterable = (
            FakeSerial(read_log)
            if simulate else
            serial.Serial(port=port_name, baudrate=baudrate, timeout=1)
        )

        with loop_iterable as ser:
            test = Test()
            test.flags = {
                'done': False,
                'inc_freq_with_fixed_step_parallel': False
            }
            while True:
                if ser.in_waiting:
                    line = ser.readline().decode(errors='replace').strip()
                    modified = proccess_line(line, test)
                    serial_log += line + '\n'

                    if modified:
                        print('>>>>> ' + line)
                        #print_test(test)
                    else:
                        print("      " + line)


                if test.flags['done']:
                    break

    except serial.SerialException as e:
        print(f"Serial Error: {e}")
    except KeyboardInterrupt:
        print("\nScanning stopped. Byeee!")

    if len(serial_log) > 0:

        if test.serial is not None:
            file_name = test.serial #modify the filename to use the serial instead

        file_path = f'dumps/{file_name}.txt'

        save_log(file_path, serial_log)


if __name__ == "__main__":

    simulate = False
    read_log = "dumps/serial-0.txt"
    selected_port = None

    if not simulate:
        ports = list_com_ports()
        selected_port = select_port(ports)

    read_serial_forever(port_name=selected_port, simulate=simulate, read_log=read_log)
