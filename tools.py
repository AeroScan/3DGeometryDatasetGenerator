import numpy as np

# Convert a float to string
def float2str(number, limit = 10) -> str:
    if abs(number) >= 10**limit:
        return ('%.' + str(limit) + 'e') % number
    elif abs(number) <= 1/(10**limit) and number != 0:
        return ('%.' + str(limit) + 'e') % number
    elif type(number) == int and number == 0:
        return str(0)
    elif number == 0.0:
        return str(0.0)
    else:
        return str(number)

# Convert a list to string
def list2str(l: list, prefix, LINE_SIZE = 90) -> str:
    l = '[' + ', '.join(float2str(n) for n in l) + ']'
    string = '' 
    last_end = -1
    last_com = 0
    for i, element in enumerate(l):
        if element == ',':
            if i > (last_end + 1 + (LINE_SIZE - len(prefix))):
                if last_end == -1:
                    string += l[last_end + 1:last_com + 1] + '\n'
                else:
                    string += prefix + l[last_end + 2: last_com + 1] + '\n'
                last_end = last_com
            last_com = i
    if last_end == -1:
        string += l[last_end + 1:len(l)]
    else:
        string += prefix + l[last_end + 2:len(l)]
    return string

# Convert a dict to string
def generateFeaturesYAML(features: dict) -> str:
    result = ''
    for key, value in features.items():
        if len(value) == 0:
            result += key + ': []\n'
            continue
        result += key + ':\n'
        
        while len(value) > 0:
            d = value[0]
            result += '- '
            for key2, value2 in d.items():
                if result[-2:] != '- ':
                    result += '  '
                result += key2 + ': '
                if type(value2).__module__ == np.__name__:
                    value2 = value2.tolist()
                if type(value2) != list:
                    result += str(value2) + '\n'
                else:
                    if len(value2) == 0:
                        result += '[]\n'
                    elif type(value2[0]) != list:
                        result += list2str(value2, '    ') + '\n'
                    else:
                        result += '\n'
                        for elem in value2:
                            result += '  - ' + list2str(elem, '    ') + '\n'
            value.pop(0)
    return result

# Convert the gpXYZ (gmsh data) to list
def gpXYZ2List(gp):
    return [gp.X(), gp.Y(), gp.Z()]

# Write string to yaml file
def writeYAML(output_name: str, features: dict):
    with open(output_name + '.yaml', 'w') as f:
        features_yaml = generateFeaturesYAML(features)
        f.write(features_yaml)