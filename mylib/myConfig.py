#!/usr/bin/python3
# -*- coding: utf-8 -*-
import configparser
import argparse
import os
import tempfile

from mylib import Url
from mylib.myDB import DB, IniDb


class CaseConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        return optionstr


def createParser():
    parser = argparse.ArgumentParser(description='Программа для переноса файлов по FTP')
    parser.add_argument('source', help='FTP откуда копируем', nargs='?')
    parser.add_argument('destination', help='куда копируем', nargs='?', default="./")
    parser.add_argument('mode', choices=['COPY', 'MOVE', 'MKDB', 'XCPY', 'XMOV', 'NONE', 'DELE'],
                        default='COPY', nargs='?',
                        help='Метод работы - копировать, переносить или только запомнить имеющиеся файлы в базе')
    '''
                    COPY - копировать
                    MOVE - переносить
                    XCPY, XMOV - копировать и переносить с заменой, даже если файл уже имеется локально
                    NONE - холостой проход
                    MKDB - файлы не скачиваются а только заносятся в БД
                    DELE - файлы удаляются на источнике без скачивания
                     
                    # допускается использовать:
                    # %d текущий день
                    # %D вчера
                    # %m текущий месяц, \%M предыдущий месяц
                    # %y текущий год, \%Y год, который был месяц назад  последние две цифры
                    # %f текущий год, \%F год, который был месяц назад целиком
                    # пример %f-%m-%d - 2019-05-27
    '''

    parser.add_argument('-c', '--config_file', help='Конфигурационный файл')
    parser.add_argument('-s', '--source', help='FTP откуда копируем')
    parser.add_argument('-d', '--destination', help='куда копируем, по умолчанию - ./')
    parser.add_argument('-M', '--mode', choices=['COPY', 'MOVE', 'MKDB', 'XCPY',
                                                 'XMOV', 'NONE', 'DELE', 'MKDB'],
                        default='COPY',
                        help='Метод работы - копировать, переносить или только запомнить имеющиеся файлы в базе')
    parser.add_argument('-m', '--mask', default='*', help='Маска, по умолчанию *')
    parser.add_argument('-n', '--name', default='ftpget', help='Имя файла БД')
    parser.add_argument('-r', '--recursive', action='store_true',
                        default=False, help='Рекурсивное копирование с сохранением структуры каталогов')
    parser.add_argument('-R', '--no_create_dir', action='store_true',
                        default=False, help='Рекурсивное копирование без сохранения структуры каталогов')
    parser.add_argument('-t', '--debug', action='store_true',
                        help='Вывод служебных сообщений протокола FTP для отладки', dest='debugging')
    parser.add_argument('-T', '--timeout', help='Таймаут при ошибке соединения', default=10, type=int)
    parser.add_argument('--retries', help='Количество попыток, 0 - бесконечно', default=10, type=int)
    parser.add_argument('--log_limit', help='Размер log файла, 0 - бесконечно', default=0, type=int)
    parser.add_argument('-l', '--log', help='Файл для записи лога')
    parser.add_argument('-j', '--concurrency', default=1, help='Количество потоков закачки', type=int)
    parser.add_argument('-D', '--database', choices=['DB', 'XDB', 'NODB'],
                        default='NODB', help='Писать в БД')
    parser.add_argument('-P', '--pid_dir', help='Каталог для размещения PID файлов', default='./')
    parser.add_argument('-p', '--passive', help='Пассивный режим', default=False, action='store_true')
    parser.add_argument('--compression', help='Compress traffic', default=False, action='store_true')
    parser.add_argument('--port', help='TCP порт, 80 для HTTP, 443 для HTTPS, '
                                       '21 для FTP, 22 для SFTP', default="Default")
    parser.add_argument('--tempdir', help=f"Папка для временных файлов, "
                                          f"если не указано то {tempfile.gettempdir()}", default=tempfile.gettempdir())
    return parser


def get_config_file(args):
    config = CaseConfigParser()
    config.read(args.config_file)
    args.name = config.get("Section", "NAM")
    args.source = Url(config.get("Section", "SRC")).full_url
    args.destination = Url(config.get("Section", "DST")).full_url
    if not args.destination.endswith('/') or args.destination.endswith(os.sep):
        args.destination += '/'
    mode = config.get("Section", "ACT")
    args.mode = mode.upper()

    flags = config.get("Section", "OTH")
    sf = flags.rstrip().split(';')
    for flag in sf:
        if flag.upper() == 'NONE':
            continue
        if flag in args.__dict__ and "=" not in flag:
            if isinstance(args.__dict__[flag], bool):
                args.__dict__[flag] = True
        if "=" in flag:
            if flag.split('=')[0] in args.__dict__:
                args.__dict__[flag.split('=')[0]] = int(flag.split('=')[1]) if flag.split('=')[1].isdigit() \
                    else flag.split('=')[1]
    args.files = dict(config.items("DB"))
    args.config = config


def get_config():
    args = createParser().parse_args()
    if args.source is None and args.config_file is None:
        print("Необходимо указать либо источник либо конфигурационный файл")
        print()
        createParser().print_help()
        # quit(1)
        return
    if args.config_file is not None:
        get_config_file(args)
    if args.no_create_dir:
        args.recursive = True
    if args.pid_dir[-1] != os.path.sep:
        args.pid_dir += os.path.sep
    args.pid_file = os.path.join(args.pid_dir, f"ftpget_{args.name}.pid")

    if args.database == "DB" or (not args.database and args.config_file):
        args.DB = IniDb(args)
        args.database = 'DB'
    else:
        args.DB = DB(args)
    return args
