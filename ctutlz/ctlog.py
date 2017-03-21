import json
try:
    # since python 3.6
    import urllib.request as urllib_request
except ImportError:
    import urllib as urllib_request
from os.path import join, isfile, dirname

from utlz import load_json, namedtuple, text_with_newlines

from ctutlz.utils.encoding import decode_from_pem, encode_to_pem
from ctutlz.utils.encoding import digest_from_pem, sha256_digest


Log = namedtuple(
    typename='Log',
    field_names=[  # each of type: str
        'description',
        'key',     # PEM encoded, type: str
        'url',
        'maximum_merge_delay',
        'operated_by',
    ],
    lazy_vals={
        'key_der': lambda self: decode_from_pem(self.key),  # type: bytes
        'id_der': lambda self: digest_from_pem(self.key),   # type: bytes
        'id_pem': lambda self: encode_to_pem(self.id_der),  # type: str
        'pubkey': lambda self: '\n'.join([                  # type: str
                              '-----BEGIN PUBLIC KEY-----',
                              text_with_newlines(text=self.key, line_length=64),
                              '-----END PUBLIC KEY-----'
        ]),
        'pubkey_hash': lambda self: sha256_digest(self.key_der),  # TODO DEVEL
    }
)


def Logs(log_dicts):
    return [Log(**kwargs) for kwargs in log_dicts]


def logs_with_operator_names(logs_dict):
    for log in logs_dict['logs']:
        operator_ids = log['operated_by']
        operator_names = [operator['name']
                          for operator
                          in logs_dict['operators']
                          if operator['id'] in operator_ids]
        log['operated_by'] = operator_names
    return Logs(logs_dict['logs'])


def download_log_list_accepted_by_chrome():
    '''Download json file with known logs accepted by chrome and return the
    logs as a list of `Log` items.
    '''
    url = 'https://www.certificate-transparency.org/known-logs/log_list.json'
    response = urllib_request.urlopen(url)
    response_str = response.read()
    try:
        data = json.loads(response_str)
    except TypeError:
        # python 3.x < 3.6
        data = json.loads(response_str.decode('utf-8'))
    return logs_with_operator_names(data)


def get_log_list():
    try:
        return get_log_list.logs  # singleton function attribute
    except AttributeError:
        package_basedir = dirname(dirname(__file__))
        filename = join(package_basedir, 'log_list.json')
        if isfile(filename):
            data = load_json(filename)
            get_log_list.logs = logs_with_operator_names(data)
        else:
            get_log_list.logs = download_log_list_accepted_by_chrome()
    return get_log_list.logs