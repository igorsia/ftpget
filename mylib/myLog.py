#!/usr/bin/python3
import sys
import logging


def get_log(args):
    log = logging.getLogger()
    log.setLevel(logging.DEBUG if args.debugging else logging.INFO)
    # log.setLevel(logging.INFO)

    # handler = logging.StreamHandler(sys.stdout)
    handler = logging.StreamHandler(open(args.log, 'a') if args.log is not None else sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(name)s[%(levelname)s] %(message)s', "%Y-%m-%d %H:%M")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    # log.info("Init Log at file %s" % (args.log if args.log is not None else "<stdout>"))
    return log


