import logging


def setup_logger():
	logger = logging.getLogger("quantforge")
	handler = logging.StreamHandler()
	formatter = logging.Formatter(
		"[%(asctime)s] [%(levelname)s] %(name)s - %(message)s",
		"%Y-%m-%d %H:%M:%S"
	)
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.setLevel(logging.INFO)
	return logger
