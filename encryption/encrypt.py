# Encode and Decoder
encoded_format = {
        '0' : 'AX35',
        '1' : 'JU68',
        '2' : 'YX70',
        '3' : 'RM26',
        '4' : 'MY72',
        '5' : 'TT37',
        '6' : 'AS70',
        '7' : 'SH37',
        '8' : 'DB66',
        '9' : 'IQ86',
        ' ' : 'MY53',
        }
def get_key(val):
        for key, value in encoded_format.items():
            if val == value:
                return key
        return "key doesn't exist"
class encrypt:

    def encode(user_input):
        
        encode_output = []
        encode_out = ''
        for i in user_input:
            if i in encoded_format:
                encode_output.append(encoded_format[i])
        for i in encode_output:
            encode_out += '' + i
            #print(i, end="")
        return encode_out

    def decode(encoded_input):
        split_input = []
        n = 4
        decode_output = []
        decode_out = ''
        for index in range(0, len(encoded_input), n):
            split_input.append(encoded_input[index: index + n])
        for i in split_input:
            decode_output.append(get_key(i))
        for i in decode_output:
            decode_out+= '' + i
            #print(i, end="")
        return decode_out