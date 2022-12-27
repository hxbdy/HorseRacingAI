import configparser

# load config
config_path = configparser.ConfigParser()
config_path.read('./src/path.ini', 'UTF-8')

config_private = configparser.ConfigParser()
config_private.read('./src/private.ini', 'UTF-8')

def path_ini(cat, path):
    '''path.iniで定義されているパスを返す
    cat: カテゴリ
    path: パス名
    '''
    return config_path.get(cat, path)

def private_ini(cat, path):
    '''private.iniで定義されているパスを返す
    cat: カテゴリ
    path: パス名
    '''
    return config_private.get(cat, path)
