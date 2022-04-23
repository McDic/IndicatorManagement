import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Union

main_logger_name = "im"
main_logger = logging.getLogger(main_logger_name)


def setup_base_logger_setting(
    path: Optional[Union[str, Path]] = None,
    max_bytes: int = 2**20,
    backup_count: int = 5,
):
    """
    Setup base logger setting.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.NOTSET)
    main_logger.setLevel(logging.NOTSET)

    formatter = logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    main_logger.addHandler(stream_handler)

    if path is not None:
        file_handler = logging.handlers.RotatingFileHandler(
            path, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        main_logger.addHandler(file_handler)

    main_logger.info("\n" + "=" * 120 + "\nSTARTING PROGRAM\n" + "=" * 120)


def get_child_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Returns child logger by given name.
    """
    if name is None or name == "__main__":
        return main_logger
    else:
        return main_logger.getChild(name)
