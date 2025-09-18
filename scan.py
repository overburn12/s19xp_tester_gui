import serial
import serial.tools.list_ports
import sys


def list_com_ports():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No COM ports found.")
        sys.exit(1)
    return ports


def select_port(ports):
    if len(ports) == 1:
        print(f"Auto-selecting COM port: {ports[0].device} - {ports[0].description}")
        return ports[0].device
    
    print("Available COM ports:")
    for i, port in enumerate(ports):
        print(f"{i}: {port.device} - {port.description}")
    
    while True:
        try:
            index = int(input("Enter the number of the COM port to use: "))
            if 0 <= index < len(ports):
                return ports[index].device
            else:
                print("Invalid number, try again.")
        except ValueError:
            print("That's not a number. Try again.")


def read_serial_data(port_name, baudrate=115200):
    try:
        with serial.Serial(port=port_name, baudrate=baudrate, timeout=1) as ser:
            print(f"Connected to {port_name}. Reading data... (Press Ctrl+C to stop)")
            while True:
                if ser.in_waiting:
                    line = ser.readline().decode(errors='replace').strip()
                    if line:
                        print(line)
    except serial.SerialException as e:
        print(f"Serial Error: {e}")
    except KeyboardInterrupt:
        print("\nStopped reading serial data.")


if __name__ == "__main__":
    ports = list_com_ports()
    selected_port = select_port(ports)
    read_serial_data(selected_port)
