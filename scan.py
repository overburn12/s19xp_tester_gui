import serial, os
#import webview, threading
import serial.tools.list_ports
import sys
import time
from datetime import datetime
from test_model import new_test, proccess_line, print_test

#-----------------------------------------------------------------------------------------------------------------------
# serial log replay
#-----------------------------------------------------------------------------------------------------------------------

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

        
def replay_log_generator(filepath, speed_up_factor = 50.0):
    prev_timestamp = None

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                timestamp_str = line.split(']')[0].strip('[')
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                if prev_timestamp:
                    delta = (timestamp - prev_timestamp).total_seconds() / speed_up_factor
                    time.sleep(max(delta, 0))
                prev_timestamp = timestamp
            except (IndexError, ValueError): #likely no timestamp present
                time.sleep(0.01) # just a small 10ms delay

            yield line


#-----------------------------------------------------------------------------------------------------------------------
# helper functions
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


def get_selected_file(dir='dumps'):
    files = [f for f in os.listdir(dir) if f.endswith('.txt')]

    if not files:
        print(f"No.txt files found in the '{dir}' directory.")
        return None
    for i, file in enumerate(files):
        print(f"{str(i).zfill(2)}: {file}")
    while True:
        try:
            selection = int(input("Enter the index of the file to open: "))
            if 0 <= selection < len(files):
                break
            else:
                print("Invalid index. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    return f"{dir}/{files[selection]}"


#-----------------------------------------------------------------------------------------------------------------------
# serial read
#-----------------------------------------------------------------------------------------------------------------------

def read_serial_forever(port_name, baudrate=115200, simulate=False, read_log=""):
    file_name = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    serial_log = ""
    test = new_test()

    try:
        loop_iterable = (
            FakeSerial(read_log)
            if simulate else
            serial.Serial(port=port_name, baudrate=baudrate, timeout=1)
        )

        with loop_iterable as ser:
            while True:
                if ser.in_waiting:
                    line = ser.readline().decode(errors='replace').strip()
                    modified = proccess_line(line, test)
                    serial_log += line + '\n'
                    if modified: #just print everything and indicate which lines modified the test object
                        print('>>>>> ' + line)
                    else:
                        print("      " + line)
                if test['flags']['done']:
                    break

    except serial.SerialException as e:
        print(f"Serial Error: {e}")
    except KeyboardInterrupt:
        print("\nScanning stopped. Byeee!")

    if len(serial_log) > 0 and not simulate:
        if test['id']['serial'] is not None:
            #modify the filename to use the serial instead
            file_name = test['id']['serial'] 
        file_path = f'dumps/{file_name}.txt'
        save_log(file_path, serial_log)

    del test['flags'] #delete flags. only needed internally for data scanning conditions
    del test['read']
    del test['psu']

    print_test(test) #print the test object when the test is over


#def start_serial_read_thread(port_name, simulate=False, read_log=""):
#    threading.Thread(target=read_serial_forever, args=(port_name, simulate, read_log), daemon=True).start()


#-----------------------------------------------------------------------------------------------------------------------
# main
#-----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    read_log = None
    selected_port = None
    
    simulate = False
    use_webview = False

    #if use_webview:
    #    window = webview.create_window("Hashboard Tester", "gui/index.html")
    #    webview.start()
    #else:
    if simulate:
        read_log = get_selected_file()
    else:
        ports = list_com_ports()
        selected_port = select_port(ports)

    read_serial_forever(port_name=selected_port, simulate=simulate, read_log=read_log)
