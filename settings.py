from configparser import *

CONFIG_FILE_NAME = 'config.txt'

class Config(ConfigParser):
    def __init__(self):
        super(Config, self).__init__()
        self.load()

    def get(self, *args, **kwargs):
        return super(Config, self).get(*args, **kwargs)

    def getboolean(self, *args, **kwargs):
        return super(Config, self).getboolean(*args, **kwargs)
    
    def getint(self, *args, **kwargs):
        return super(Config, self).getint(*args, **kwargs)

    def getfloat(self, *args, **kwargs):
        return super(Config, self).getfloat(*args, **kwargs)

    def load(self):
        try:
            self.read_file(open(CONFIG_FILE_NAME))

        except (FileNotFoundError, IOError):
            print('No config file found, generating from defaults')
            self.create_default_conf()

    def create_default_conf(self):
        self['application_status'] = {
            'MAT':      'False',
            'LIGHT':    'False',
            'FOGGER':   'False'}
        self['probe'] = {
            'READ_DIRECTORY':   ''}
        self['mat_bounds'] = {
            'LOWER':  '',
            'TARGET':       '',
            'UPPER':  '',
            'DANGER_ZONE':  ''}
        self['ambient_bounds'] = {
            'LOWER':  '',
            'TARGET':       '',
            'UPPER':  '',
            'DANGER_ZONE':  '',}
        self['humidity_bounds'] = {
            'LOWER':  '',
            'UPPER':  ''}
        self['external'] = {
            'PUSHBULLET_TOKEN': '',
            'PUSHBULLET_URL':   ''}
        self['alert'] = {
            'CONCURRENT_READ_FAILURE_ALERT_THRESHOLD':  '10'}
        self['save_file'] = {
            'NAME': '.enviro_manager_pickle'}
        self.save_config()

    def save_config(self):
        with open(CONFIG_FILE_NAME, 'w') as configfile:
            self.write(configfile)
