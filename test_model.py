from dataclasses import dataclass, asdict
from typing import Dict, Optional
from pprint import pprint

@dataclass
class Test:
    model: str | None = None
    serial: str | None = None
    chip_bin: int | None = None
    miner_type: str | None = None
    asic_type: str | None = None
    max_asic: int = 0
    fan_speed: int = 0
    
    real_freq: float = 0.0
    want_freq: float = 0.0

    temp_max: Optional[int] = None
    temp_target: Optional[int] = None

    apw_on: bool = False

    asic_okay: bool = False
    nonce_rate_okay: bool = False
    eeprom_okay: bool = False

    voltage: int = 0
    frequency: int = 0
    valid_nonce_num: int = 0
    repeat_nonce_num: int = 0

    flags: Dict | None = None


def proccess_line(line, test):

    def get_value(line, split_char):
        return line.split(split_char)[-1].strip()

    before = asdict(test)

    if'edf_v4_dump_data' in line:
        if 'board_sn' in line:
            test.serial = get_value(line, "=")
        if 'board_name' in line:
            test.model = get_value(line, "=")
        if 'chip_bin' in line:
            test.chip_bin = int(get_value(line, "="))

    if 'parse_MES_system_information' in line:
        if 'Miner_Type' in line:
            test.miner_type = get_value(line, ":")
        if ' Asic_Type' in line:
            test.asic_type = get_value(line, ":")
        if ' Asic_Num ' in line:
            test.max_asic = int(get_value(line, ":"))
        if 'Fan_Speed' in line:
            test.fan_speed = int(get_value(line, ":"))

    if '_power_down' in line:
        test.apw_on = False

    if 'gHistory_Result' in line:
        if 'asic_okay' in line:
            test.asic_okay = get_value(line, ":") == 'true'
        if 'nonce_rate_okay' in line:
            test.nonce_rate_okay = get_value(line, ":") == 'true'
        if 'eeprom_ok' in line:
            test.eeprom_okay = get_value(line, ":") == 'true'
        if '.voltage' in line:
            test.voltage = int(get_value(line, ":"))
        if 'frequency' in line:
            test.frequency = int(get_value(line, ":"))
        if 'valid_nonce_num' in line:
            test.valid_nonce_num = int(get_value(line, ":"))
        if 'repeat_nonce_num' in line:
            test.repeat_nonce_num = int(get_value(line, ":"))

    if 'APW_power_on' in line:
        val = get_value(line, ":")
        if 'APW_power_on' in val:
            test.apw_on = True
        if 'voltage' in line:
            test.voltage = int(float(get_value(line, " "))) * 100


    if test.flags['inc_freq_with_fixed_step_parallel']:
        try:
            parts = line.split(',')
            for part in parts:
                if 'Real freq' in part:
                    test.real_freq = float(part.split(':')[-1].strip())
                if 'Want freq' in part:
                    test.want_freq = float(part.split(':')[-1].strip())
        except Exception as e:
            print(f"Failed to parse real freq: {e}")
        test.flags['inc_freq_with_fixed_step_parallel'] = False

    if 'inc_freq_with_fixed_step_parallel' in line:
        test.flags['inc_freq_with_fixed_step_parallel'] = True

    if 'Single_Board_PT2_Software_Pattern_Test' in line:
        if 'wait temp,max:' in line:
            try:
                pairs = line.split('wait temp,')[-1].split(',')
                for pair in pairs:
                    key, val = pair.split(':')
                    key = key.strip().lower()
                    val = val.strip()
                    if key == 'max':
                        test.temp_max = int(val)
                    elif key == 'target':
                        test.temp_target = int(val)
            except Exception as e:
                print(f"Failed to parse temp info: {e}")

    if 'main :' in line:
        if 'TEST OVER' in line:
            test.flags['done'] = True

    # Compare before and after
    after = asdict(test)
    modified = before != after

    return modified

def print_test(test):
    pprint(asdict(test), sort_dicts=False)
    print("----------------------------------------------")