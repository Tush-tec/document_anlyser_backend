import logging, sys
def setup_logging():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='{"ts":"%(asctime)s","lvl":"%(levelname)s","mod":"%(name)s","msg":%(message)s}',
    )