import serial
import serial.tools.list_ports
import sys
from dataclasses import dataclass

@dataclass
class Test:
    model: str | None = None
    serial: str | None = None
    chip_bin: int | None = None
    miner_type: str | None = None
    asic_type: str | None = None
    max_asic: int = 0

    apw_on: bool = False

    asic_okay: bool = False
    nonce_rate_okay: bool = False
    eeprom_okay: bool = False

    voltage: int = 0
    frequency: int = 0
    valid_nonce_num: int = 0
    repeat_nonce_num: int = 0



def proccess_line(line):

    def get_value(line, split_char):
        return line.split(split_char)[-1].strip()
    
    test = Test()
    modified = True

    print(f"> {line}") #just print every line for now to debug

    if'edf_v4_dump_data' in line:
        if 'board_sn' in line:
            test.board_serial = get_value(line, "=")
        if 'board_name' in line:
            test.board_model = get_value(line, "=")
        if 'chip_bin' in line:
            test.chip_bin = int(get_value(line, "="))
    elif 'parse_MES_system_information' in line:
        if 'Miner_Type' in line:
            test.miner_type = get_value(line, ":")
        if ' Asic_Type' in line:
            test.asic_type = get_value(line, ":")
        if 'Asic_Num' in line:
            test.max_asic = get_value(line, ":")
    elif '_power_down' in line:
        test.apw_on = False
    elif 'gHistory_Result' in line:
        if 'asic_okay' in line:
            test.asic_okay = get_value(line, ":") == 'true'
        if 'nonce_rate_okay' in line:
            test.nonce_rate_okay = get_value(line, ":") == 'true'
        if 'eeprom_ok' in line:
            test.eeprom_okay = get_value(line, ":") == 'true'
        if 'voltage' in line:
            test.voltage = int(get_value(line, ":"))
        if 'frequency' in line:
            test.frequency = int(get_value(line, ":"))
        if 'valid_nonce_num' in line:
            test.valid_nonce_num = int(get_value(line, ":"))
        if 'repeat_nonce_num' in line:
            test.repeat_nonce_num = int(get_value(line, ":"))
    elif 'APW_power_on' in line:
        val = get_value(line, ":")
        if 'APW_power_on' in val:
            test.apw_on = True
        if 'voltage' in line:
            test.voltage = int(get_value(line, " ")) * 100
    else:
        modified = False   
        
    if modified:
        print("DATA UPDATED") #send out the updated data



def list_com_ports():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No COM ports found. Womp womp.")
        sys.exit(1)
    print("Available COM ports:")
    for i, port in enumerate(ports):
        print(f"{i}: {port.device} - {port.description}")
    return ports

def select_port(ports):
    while True:
        try:
            index = int(input("Enter the number of the COM port to use: "))
            if 0 <= index < len(ports):
                return ports[index].device
            else:
                print("Invalid number, try again.")
        except ValueError:
            print("That ain't a number. Try again.")

def read_serial_forever(port_name, baudrate=115200, log_file="serial.txt"):
    try:

        with serial.Serial(port=port_name, baudrate=baudrate, timeout=1) as ser:
            while True:
                if ser.in_waiting:
                    line = ser.readline().decode(errors='replace').strip()
                    proccess_line(line)

    except serial.SerialException as e:
        print(f"Serial Error: {e}")
    except KeyboardInterrupt:
        print("\nScanning stopped. Byeee!")

if __name__ == "__main__":
    ports = list_com_ports()
    selected_port = select_port(ports)
    read_serial_forever(selected_port)
