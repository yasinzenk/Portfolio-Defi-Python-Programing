import logging
import sys

def setup_logging(log_level: str = "INFO", log_file: str = "portfolio_analyzer.log") -> logging.Logger:
    """
    Configure logging with separate console and file handlers.

    Console  : clean messages (no timestamp, no logger name).
    File     : detailed messages for debugging.
    """
    root_logger = logging.getLogger()
    if root_logger.handlers:
        # Avoid adding handlers twice if setup_logging is called multiple times
        return root_logger

    root_logger.setLevel(logging.DEBUG)

    # --- Console handler: clean output, like your old prints ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO) 

    # --- File handler: full debug info ---
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG) 

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    return root_logger

