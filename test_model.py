import copy, pprint

def new_test():
    return {
        'serial': None,
        'model': None,
        'chip_bin': None,
        'miner_type': None,
        'asic_type': None,
        'max_asic': None,
        'fan_speed': None,
        'real_freq': None,
        'want_freq': None,
        'dummy_data_asic': None,
        'temp_max': None,
        'temp_target': None,
        'apw_on': False,
        'asic_okay': False,
        'nonce_rate_okay': False,
        'eeprom_okay': False,
        'voltage': None,
        'frequency': None,
        'valid_nonce_num': None,
        'repeat_nonce_num': None,
        'flags': {
            'done': False,
            'inc_freq_with_fixed_step_parallel': False,
            'Find dummy data': False
        }
    }


def deep_compare(obj1, obj2):
    if type(obj1)!= type(obj2):
        return False
    if isinstance(obj1, dict):
        if set(obj1.keys())!= set(obj2.keys()):
            return False
        for key in obj1:
            if not deep_compare(obj1[key], obj2[key]):
                return False
        return True
    elif isinstance(obj1, (list, tuple)):
        if len(obj1)!= len(obj2):
            return False
        for i in range(len(obj1)):
            if not deep_compare(obj1[i], obj2[i]):
                return False
        return True
    else:
        return obj1 == obj2


def proccess_line(line, test):
    def get_value(line, split_char):
        return line.split(split_char)[-1].strip()

    before = copy.deepcopy(test)

    if 'BTC_check_register' in line:
        if 'Find dummy data' in line:
            test.flags['Find dummy data'] = True

        #[1970-01-01 00:05:11.471] BTC_check_register : reg_value = 0x01040000, which_asic = 0, reg_address = 0x00000040
        sections = line.split(':')
        for section in sections:
            if ',' in section:
                subsections = section.split(',')
                for subsection in subsections:
                    if 'which_asic' in subsection:
                        data_strs = subsection.split('=')
                        test['dummy_data_asic'] = int(data_strs[1].strip())

    if'edf_v4_dump_data' in line:
        if 'board_sn' in line:
            test['serial'] = get_value(line, "=")
        if 'board_name' in line:
            test['model'] = get_value(line, "=")
        if 'chip_bin' in line:
            test['chip_bin'] = int(get_value(line, "="))

    if 'parse_MES_system_information' in line:
        if 'Miner_Type' in line:
            test['miner_type'] = get_value(line, ":")
        if ' Asic_Type' in line:
            test['asic_type'] = get_value(line, ":")
        if ' Asic_Num ' in line:
            test['max_asic'] = int(get_value(line, ":"))
        if 'Fan_Speed' in line:
            test['fan_speed'] = int(get_value(line, ":"))

    if '_power_down' in line:
        test['apw_on'] = False

    if 'gHistory_Result' in line:
        if 'asic_ok' in line:
            test['asic_okay'] = get_value(line, ":") == 'true'
        if 'nonce_rate_ok' in line:
            test['nonce_rate_okay'] = get_value(line, ":") == 'true'
        if 'eeprom_ok' in line:
            test['eeprom_okay'] = get_value(line, ":") == 'true'
        if '.voltage' in line:
            test['voltage'] = int(get_value(line, ":"))
        if 'frequency' in line:
            test['frequency'] = int(get_value(line, ":"))
        if 'valid_nonce_num' in line:
            test['valid_nonce_num'] = int(get_value(line, ":"))
        if 'repeat_nonce_num' in line:
            test['repeat_nonce_num'] = int(get_value(line, ":"))

    if 'APW_power_on' in line:
        val = get_value(line, ":")
        if 'APW_power_on' in val:
            test['apw_on'] = True
        if 'voltage' in line:
            test['voltage'] = int(float(get_value(line, " "))) * 100


    if test['flags']['inc_freq_with_fixed_step_parallel']:
        try:
            parts = line.split(',')
            for part in parts:
                if 'Real freq' in part:
                    test['real_freq'] = float(part.split(':')[-1].strip())
                if 'Want freq' in part:
                    test['want_freq'] = float(part.split(':')[-1].strip())
        except Exception as e:
            print(f"Failed to parse real freq: {e}")
        if '[' in line:
            test['flags']['inc_freq_with_fixed_step_parallel'] = False

    if 'inc_freq_with_fixed_step_parallel' in line:
        test['flags']['inc_freq_with_fixed_step_parallel'] = True

    if 'Single_Board_PT2_Software_Pattern_Test' in line:
        if 'wait temp,max:' in line:
            try:
                pairs = line.split('wait temp,')[-1].split(',')
                for pair in pairs:
                    key, val = pair.split(':')
                    key = key.strip().lower()
                    val = val.strip()
                    if key == 'max':
                        test['temp_max'] = int(val)
                    elif key == 'target':
                        test['temp_target'] = int(val)
            except Exception as e:
                print(f"Failed to parse temp info: {e}")

    if 'main :' in line:
        if 'TEST OVER' in line:
            test['flags']['done'] = True

    # Compare before and after
    modified = deep_compare(before, test)

    return modified

def print_test(test):
    pprint.pprint(test)
    print("----------------------------------------------")