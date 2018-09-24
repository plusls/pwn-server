def get_pwn_data(token):
    '''参数为token 返回该token对应的题目名和flag 以及该题的image_tag'''
    if token == 'note_01':
    	return ('note', "cnss{it_is_note_01}", 'cnss/pwn')
    elif token == 'note_02':
        return ('note', 'cnss{it_is_note_02}', 'cnss/pwn')
    if token == 'pwn1_01':
    	return ('pwn1', "cnss{it_is_pwn1}", 'cnss/pwn')
    if token == 'sh':
        return ('sh', 'cnss{test_hahah}', 'cnss/pwn')
    return('', '', '')