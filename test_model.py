import copy, pprint

def new_test():
    return {
        'id':{
            'serial': None,
            'model': None,
            'chip_bin': None,
            'frequency': None,
            'miner_type': None,
            'asic_type': None,
            'max_asic': None
        },
        'psu': {
            'apw_on': None,
            'voltage': None
        },
        'results': {
            'faulty_asic_register': {
                'reported_asic': None,
                'find': False
            },
            'nonce':{
                'pattern_nonce': None,
                'valid_nonce_num': None,
                'nonce_rate': None,
                'repeat_nonce_num': None,
                'lost_nonce': None,
                'nonce_map': {}
            },
            'ok':{
                'eeprom_ok': None,
                'asic_ok': None,
                'nonce_rate_ok': None
            },
            'asic_found': None,
            'bad_asics': []
        },
        'read': {
            'temp_current': None,
            'temp_target': None,
            'real_freq': None,
            'target_freq': None
        },
        'flags': {
            'done': False,
            'inc_freq_with_fixed_step_parallel': False,
            'bad_asic_list': False,
            'clear_all_thread': False
        }
    }


def deep_compare(a, b):
    if type(a) != type(b):
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(deep_compare(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(deep_compare(x, y) for x, y in zip(a, b))
    return a == b


def proccess_line(line, test):
    def get_value(line, split_char):
        return line.split(split_char)[-1].strip()

    before = copy.deepcopy(test)

    if 'BTC_check_register' in line:
        if 'Find dummy data' in line:
            test['results']['faulty_asic_register']['find'] = True

        #[1970-01-01 00:05:11.471] BTC_check_register : reg_value = 0x01040000, which_asic = 0, reg_address = 0x00000040
        if 'which_asic' in line:
            sections = line.split(':')
            for section in sections:
                if ',' in section:
                    subsections = section.split(',')
                    for subsection in subsections:
                        if 'which_asic' in subsection:
                            data_strs = subsection.split('=')
                            test['results']['faulty_asic_register']['reported_asic'] = int(data_strs[1].strip())

    if'edf_v4_dump_data' in line:
        if 'board_sn' in line:
            test['id']['serial'] = get_value(line, "=")
        if 'board_name' in line:
            test['id']['model'] = get_value(line, "=")
        if 'chip_bin' in line:
            test['id']['chip_bin'] = int(get_value(line, "="))
        if 'frequency = ' in line:
            test['id']['frequency'] = int(get_value(line, "="))

    if 'parse_MES_system_information' in line:
        if 'Miner_Type' in line:
            test['id']['miner_type'] = get_value(line, ":")
        if ' Asic_Type' in line:
            test['id']['asic_type'] = get_value(line, ":")
        if ' Asic_Num ' in line:
            test['id']['max_asic'] = int(get_value(line, ":"))

    if '_power_down' in line:
        test['psu']['apw_on'] = False
        test['psu']['voltage'] = 0

    if 'gHistory_Result' in line:
        if 'asic_ok' in line:
            test['results']['ok']['asic_ok'] = get_value(line, ":") == 'true'
        if 'nonce_rate_ok' in line:
            test['results']['ok']['nonce_rate_ok'] = get_value(line, ":") == 'true'
        if 'eeprom_ok' in line:
            test['results']['ok']['eeprom_ok'] = get_value(line, ":") == 'true'
        if 'frequency' in line:
            test['read']['frequency'] = int(get_value(line, ":"))
        if 'valid_nonce_num' in line:
            test['results']['nonce']['valid_nonce_num'] = int(get_value(line, ":"))
        if 'repeat_nonce_num' in line:
            test['results']['nonce']['repeat_nonce_num'] = int(get_value(line, ":"))
        if '.nonce_rate:' in line:
            test['results']['nonce']['nonce_rate'] = float(get_value(line, ":"))

    if test['flags']['bad_asic_list']:
        #todo: add bad asic list population here
        if '----------' in line:
            test['flags']['bad_asic_list'] = False

    if test['flags']['clear_all_thread']:
        if '1970-01-01' in line:
            test['flags']['clear_all_thread'] = False
        elif '   ' in line:
            status_pairs = line.split('   ')
            for pair in status_pairs:
                index = pair.split(']')[0].replace('[', '')
                status = pair.split(']')[1].strip()
                if status == 'X':
                    test['results']['bad_asics'].append(index)

    if 'clear_all_thread' in line:
        test['flags']['clear_all_thread'] = True

    if 'get_result :' in line:
        if 'lost nonce number' in line:
            test['results']['nonce']['lost_nonce'] = int(get_value(line, "="))
        if 'bad asic list:' in line:
            test['flags']['bad_asic_list'] = True

    if False:
        if 'asic[' in line:
            #print ('YO: ' + line)
            assignments = [x.strip() for x in line.split(',') if x.strip()]
            for assignment in assignments:
                left, right = assignment.split('=')
                index = left.strip().replace('asic[', '').replace(']', '')
                nonce_count = int(right.strip())
                test['results']['nonce']['nonce_map'][index] = nonce_count

    if 'APW_power_on' in line:
        val = get_value(line, ":")
        if 'APW_power_on' in val:
            test['psu']['apw_on'] = True
        if 'voltage' in line:
            test['psu']['voltage'] = int(float(get_value(line, " "))) * 100

    if test['flags']['inc_freq_with_fixed_step_parallel']:
        try:
            parts = line.split(',')
            for part in parts:
                if 'Real freq' in part:
                    test['read']['real_freq'] = float(part.split(':')[-1].strip())
                if 'Want freq' in part:
                    test['read']['target_freq'] = float(part.split(':')[-1].strip())
        except Exception as e:
            print(f"Failed to parse real freq: {e}")
        if '[' in line:
            test['flags']['inc_freq_with_fixed_step_parallel'] = False

    if 'inc_freq_with_fixed_step_parallel' in line:
        test['flags']['inc_freq_with_fixed_step_parallel'] = True

        #[1970-01-01 00:11:04.719] get_register_value : reg_value_num: 108
    if 'Single_Board_PT2_Software_Pattern_Test' in line:
        if 'find' in line:
            parts = line.split(":")
            for part in parts:
                if 'find' in part:
                    words = part.split()
                    for word in words:
                        if word.isdigit():
                            test['results']['asic_found'] = int(word)

        if 'wait temp,max:' in line:
            try:
                pairs = line.split('wait temp,')[-1].split(',')
                for pair in pairs:
                    key, val = pair.split(':')
                    key = key.strip().lower()
                    val = val.strip()
                    if key == 'max':
                        test['read']['temp_current'] = int(val)
                    elif key == 'target':
                        test['read']['temp_target'] = int(val)
            except Exception as e:
                print(f"Failed to parse temp info: {e}")

    if 'PT2_show_status_func' in line:
        if 'gValid_Nonce_Num' in line:
            test['results']['nonce']['valid_nonce_num'] = int(get_value(line, '='))

    #[1970-01-01 00:07:03.795] software_pattern_8_midstate_send_function : Send test 786720 pattern done
    if 'software_pattern_8_midstate_send_function' in line:
        if ': Send test' in line:
            line_after_timestamp = line.split(']')[1]
            line_after_colon = line_after_timestamp.split(':')[1]
            elements = line_after_colon.split()
            for element in elements:
                if element.isdigit():
                    test['results']['nonce']['pattern_nonce'] = element

    #[1970-01-01 00:16:19.973] find_submit_history_result_index : We had do 1 tests, and strict standard are not ok
    if 'find_submit_history_result_index' in line:
        if 'strict standard are not ok' in line:
            test['results']['nonce']['lost_nonce'] = int(test['results']['nonce']['pattern_nonce']) - int(test['results']['nonce']['valid_nonce_num'])
            test['results']['nonce']['nonce_rate'] = float(int(test['results']['nonce']['valid_nonce_num']) / int(test['results']['nonce']['pattern_nonce']))

    if 'main :' in line:
        if 'TEST OVER' in line:
            test['flags']['done'] = True

    return not deep_compare(before, test)

def print_test(test):
    pprint.pprint(test)
    print("----------------------------------------------")