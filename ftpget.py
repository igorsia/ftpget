#!/usr/bin/env python3
import os
import threading
from queue import Queue
from datetime import datetime as dt
import signal
import atexit
from time import sleep

from mylib import full_stack, Url, get_log, get_config, Target, FtpTarget, SftpTarget, LocalTarget

'''
ОШИБКИ
1 - Ошибка выыполнения, программа неожиданно прекратила работу
2 - Неописаный тип URL
3 - Ошибка параметров коммандной строки
4 - Ошибка доступа к исходному ресурсу.
5 - Ошибка {e} доступа к целевому ресурсу.
7 - Процесс уже запущен
42 - Прерывание работы по Ctrl-C
'''


def clear_inidb(target):
    if target.args.database == "DB":
        for item in target.args.files:
            for s_item in item.split('/'):
                if target.is_correspond(s_item):
                    break
            else:
                target.args.config.remove_option("DB", item)
                # target.Log.info(f"remove item {item=}")
        target.args.DB.write_db()


def new_target(url):
    type_url = Url(url)[0]
    Target.log.debug(f"{Url=}")
    try:
        if type_url == "ftp":
            target = FtpTarget(url)
        elif type_url == "file":
            target = LocalTarget(url)
        elif type_url == "sftp":
            target = SftpTarget(url)
        else:
            Target.log.error("Неописаный тип URL в", url)
            quit(2)
    except Exception as e:
        Target.log.error("ошибка создания объекта типа ->", str(e))
        raise TypeError
    # self.Log.debug("создан тип цели",type_url)
    return target


def get_files(target: Target, queue: Queue):
    while True:
        # Получаем url из очереди
        url = queue.get()
        try:
            target.log.debug(f"{threading.current_thread().name} - get_files {url}")
            target.get_file(url)
        except Exception as e:
            target.log.error(f"{threading.current_thread().name} - get_files error {e} {url}")
            target.log.error(full_stack())
            target.reconnect()
        finally:
            queue.task_done()


def move_between_queues(target: Target, queue_in: Queue, queue_out: Queue):
    while True:
        item = queue_in.get()
        target.log.debug(f"{threading.current_thread().name} - move_between_queues {item}")
        queue_out.put(item)
        queue_in.task_done()


def get_dirs(target: Target, in_queue: Queue, temp_queue: Queue, file_queue: Queue):
    while True:
        # Получаем url из очереди
        url = in_queue.get()
        # Выполняем загрузку файла или списка файлов
        answ = target.list(url)
        target.log.debug(f"{threading.current_thread().name} - list {url} -> {answ}")
        for item in answ:
            if item[-1] in ['/', os.sep] and target.args.recursive:
                temp_queue.put(item)
            elif item[-1] in ['/', os.sep]:
                ...
            else:
                file_queue.put(item)
        in_queue.task_done()


def check_pid(pid_file):
    pid = os.getpid()
    # FileName = "ftpget_"+args.name
    if os.path.exists(pid_file):
        return True
    with open(pid_file, 'w+') as pid_file:
        pid_file.write(str(pid))
    pid_file.close()
    return False


def main():
    def finish():
        clear_inidb(src_target)
        os.remove(args.pid_file)
        args.DB.write_db()

    """
    Запускаем программу
    """
    now = dt.now()
    absolute_time_start = now.strftime('%Y-%m-%d %H:%M:%S')

    # Загружаем параметры командной строки
    args = get_config()
    if args is None:
        quit(3)
    url = Url(args.source)

    # Инициализируем логгер
    log = get_log(args)
    Target.log = log
    log.name = args.name
    log.info("Запуск в %s" % absolute_time_start)

    # srcUrl = 'ftp://anonymous:mail@local.net@ftp.cisco.com/pub/mibs/*'
    # srcUrl = 'ftp://andy:andy00@192.168.10.39/home/andy/igor/*'
    '''
    # ftp://mirror.yandex.ru/ubuntu/pool/main/liba/libaal/ -> ftp://mirror.yandex.ru/ubuntu/pool/main/liba/libaal/*
    # ftp://mirror.yandex.ru/ubuntu/pool/main/liba/libaal может быть как файлом так и каталогом
    1. Проверяем существует ли элемент по этому пути. Если нет -> ftp://mirror.yandex.ru/ubuntu/pool/main/liba/libaal/*
    2. Если элемент существует проверяем isDir -> ftp://mirror.yandex.ru/ubuntu/pool/main/liba/libaal/*
    3. Иначе это файл -> ftp://mirror.yandex.ru/ubuntu/pool/main/liba/libaal
    # ftp://mirror.yandex.ru/ubuntu/pool/main/liba/libaal/* -> Не трогаем
    # ftp://mirror.yandex.ru/ubuntu/pool/main/liba/lib* -> Не трогаем
    '''
    log.debug(f"{args.source}=>{args.destination}")
    if args.source[-1] == "/" and Url(args.source).type_url != "file":
        args.source += "*"

    Target.args = args
    Target.log = log
    try:
        dst_target = new_target(args.destination)
    except Exception as e:
        log.error(f'Ошибка {e} доступа к исходному ресурсу.')
        quit(4)
        
    try:
        src_target = new_target(args.source)
    except Exception as e:
        log.error(f'Ошибка {e} доступа к целевому ресурсу.')
        quit(5)
        
    Target.destination = dst_target

    atexit.register(finish)

    def sigint_handler(*kwargs):
        log.info("Ctrl+C exit")
        quit(42)

    try:
        if check_pid(args.pid_file):
            log.info("Процесс уже запущен")
            quit(7)
    except Exception as e:
        log.info(e)

    signal.signal(signal.SIGINT, sigint_handler)

    dirs_queue = Queue()  # Очередь на получение списка файлов
    files_queue = Queue()  # Очередь файлов на загрузку
    temp_queue = Queue()  # Промежуточная очередь

    # Даем очереди нужные нам ссылки для скачивания
    dirs_queue.put(args.source)
    t = threading.Thread(target=get_dirs, args=(src_target, dirs_queue, temp_queue, files_queue,), daemon=True)
    t.start()
    # Запускаем очереди получения файлов
    for _ in range(args.concurrency):
        t = threading.Thread(target=get_files, args=(new_target(args.source), files_queue,), daemon=True)
        t.start()

    # Запускаем вспомогательную очередь
    t = threading.Thread(target=move_between_queues, args=(src_target, temp_queue, dirs_queue,), daemon=True)
    t.start()

    # Ждем завершения работы очередей
    '''
    while True:
        with (dirs_queue.mutex, files_queue.mutex, temp_queue.mutex):
            if dirs_queue.unfinished_tasks == 0 and \
                    files_queue.unfinished_tasks == 0 and \
                    temp_queue.unfinished_tasks == 0:
                break
    '''
    while True:
        # with (dirs_queue.mutex, temp_queue.mutex, files_queue.mutex):
        dirs_queue.mutex.acquire()
        temp_queue.mutex.acquire()
        files_queue.mutex.acquire()
        if dirs_queue.unfinished_tasks == 0 and \
           temp_queue.unfinished_tasks == 0 and \
           files_queue.unfinished_tasks == 0:
            break
        elif files_queue.unfinished_tasks != 0:
            files_queue.mutex.release()
            temp_queue.mutex.release()
            dirs_queue.mutex.release()
            files_queue.join()
        elif temp_queue.unfinished_tasks != 0:
            files_queue.mutex.release()
            temp_queue.mutex.release()
            dirs_queue.mutex.release()
            temp_queue.join()
        elif dirs_queue.unfinished_tasks != 0:
            files_queue.mutex.release()
            temp_queue.mutex.release()
            dirs_queue.mutex.release()
            dirs_queue.join()

    log.info("Успешное завершение программы")

    if args.log_limit != 0:
        # Target.Log.info(f"Усекаем {args.log} до {args.log_limit} строк")
        os.system(f"tail -n{args.log_limit} {args.log} > {args.log}.temp")
        os.system(f"mv {args.log}.temp {args.log}")

    clear_inidb(src_target)

    log.info("Успешное завершение программы")
    sleep(1)
    print(f"Успешное завершение программы в {dt.now():%F %T}")


if __name__ == "__main__":
    main()
