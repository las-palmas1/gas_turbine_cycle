import numpy as np
import logging.config


def create_logger(name=__name__, loggerlevel=logging.INFO, add_file_handler=True,
                  add_console_handler=True, filename='logfile.log', filemode='a', add_datetime=False,
                  add_module_name=False):
    logger = logging.getLogger(name)
    logger.setLevel(loggerlevel)
    logger.propagate = 0
    datetime_template = '%(asctime)s - ' * add_datetime
    module_name_template = '%(name)s - ' * add_module_name
    fmt = datetime_template + module_name_template + '%(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt=fmt,
                                  datefmt='%d\%m\%Y %H:%M:%S')
    if add_console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.NOTSET)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    if add_file_handler:
        file_handler = logging.FileHandler(filename, mode=filemode)
        file_handler.setLevel(logging.NOTSET)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


def eta_comp_stag(pi_comp_stag, k, eta_comp_stag_p):
    """Адиабатический КПД компрессора в зависимости от политропического"""
    return (pi_comp_stag ** ((k - 1) / k) - 1) / (pi_comp_stag ** ((k - 1) / (k * eta_comp_stag_p)) - 1)


def eta_turb_stag(pi_turb_stag, k, eta_turb_stag_p):
    """Адиабатический КПД турбины в зависимости от политропического"""
    return (1 - pi_turb_stag ** ((1 - k) * eta_turb_stag_p / k)) / (1 - pi_turb_stag ** ((1 - k) / k))


def eta_turb_l(eta_turb_stag, H_turb_stag, H_turb, c_out):
    """Лопаточный КПД турбины через КПД по параметрам торможения"""
    return eta_turb_stag * H_turb_stag / H_turb + c_out ** 2 / (2 * H_turb)
