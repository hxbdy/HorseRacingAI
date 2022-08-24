import logging

# debug initialize
# LEVEL : DEBUG < INFO < WARNING < ERROR < CRITICAL
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# DEBUG ログを無効
logging.disable(logging.DEBUG)

# INFO レベル以下のログを無効
# logging.disable(logging.INFO)

# WARNING レベル以下のログを無効
# logging.disable(logging.WARNING)

# ERROR レベル以下のログを無効
# logging.disable(logging.ERROR)
