import os
from urllib.parse import urlparse

def is_mask(mask):
    if "*" in mask or "(" in mask or "[" in mask or "%" in mask:
        return True
    return False

class Url:
    def __init__(self, url: str):
        """
        :param url:
        """

        """
        ftp://user:user_passw@ftp_server/path/to/files/%f/%f-%m/%f-%m-%D/trg_%D%m%y_*.gz
        url_type://user:password@host:port/path/to/files/mask
        url_type
        user
        password
        host
        port
        path
        mask
        """

        if isinstance(url, Url):
            self._type_url = url.type_url
            self._user = url.user
            self._passw = url.passw
            self._host = url.host
            self._port = url.port
            self._path = url.path
            self._mask = url.mask
            return
        if url.endswith('/') or url.endswith(os.sep):
            url += '*'
        parsed_url = urlparse(url)
        if '://' not in url:  # Это у нас обычный файловый путь вместо урла
            type_url = "file"
        else:
            type_url = parsed_url.scheme

        if type_url == "file":
            host = ''
            user = ''
            passw = ''
            port = ''
            i = 0
            path = parsed_url.netloc + parsed_url.path
            for i, item in enumerate(path.split('/')):
                if is_mask(item):
                    break
            splitted_path = path.split(os.sep)
            path = os.sep.join(splitted_path[:i]) + os.sep
            mask = os.sep.join(splitted_path[i:])
        else:
            host = parsed_url.hostname
            user = parsed_url.username
            passw = parsed_url.password
            port = parsed_url.port
            # /dir/to/files*/with/mask*
            # path = /dir/to/
            # mask = files*/with/mask*
            i = 0
            for i, item in enumerate(parsed_url.path.split('/')):
                if is_mask(item):
                    break
            splitted_path = parsed_url.path.split('/')
            path = '/'.join(splitted_path[:i]) + '/'
            mask = '/'.join(splitted_path[i:])

            if user is None:  # если логина и пароля нет то анонимный вход
                user = "anonymous"
                passw = "mail@local.net"
            if passw is None:
                passw = ''

        if mask == "":
            mask = "*"

        self._type_url = type_url
        self._user = user
        self._passw = passw
        self._host = host
        self._port = port
        self._path = path
        self._mask = mask

    def __getitem__(self, key):
        return (self.type_url, self._user, self._passw, self._host, self._path, self._mask)[key]

    @property
    def type_url(self):
        return self._type_url

    @property
    def user(self):
        return self._user

    @property
    def passw(self):
        return self._passw

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def path(self):
        return self._path

    @property
    def mask(self):
        return self._mask

    @property
    def file(self):
        return '' if is_mask(self._mask) else self._mask

    @property
    def url(self):
        return f"{self._type_url}://{self.host}{self.path}{self.mask}"

    @property
    def full_url(self):
        if self._type_url == 'file':
            return self.url
        return f"{self._type_url}://{self.user}:{self.passw}@{self.host}{self.path}{self.mask}"

    @property
    def full_path(self):
        return f"{self._type_url}://{self.host}{self.path}"

    @property
    def str(self):
        return self.full_url

    def __len__(self):
        return 6

    def __call__(self, url):
        return self._type_url, self.user, self.passw, self.host, self.path, self.mask

    def __str__(self):
        return self.full_url

    def __repr__(self):
        return (f"Object Url: {self._type_url=}://{self.user=}:{self.passw=}@"
                f"{self.host=}:{self._port=}{self.path=}{self.mask=}")