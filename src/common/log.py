# ロガー設定
# ログファイルはレベルWARNING以上のみが記録される
# コンソールはレベルDEBUG以上のみが出力される
# ファイルの最初でimportしてください

import json
import logging
import logging.config

from rich.logging import RichHandler
from rich.console import Console

CONFIG = '''
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "simple_format": {
            "format": "%(asctime)s %(filename)23s [%(levelname)10s] %(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "formatter": "simple_format",
            "filename": "./dst/log/output.log",
            "mode": "w",
            "level": "WARNING"
        },
        "rich": {
            "class": "rich.logging.RichHandler",
            "level": "DEBUG",
            "rich_tracebacks": "True"
        }
    },
    "root": {
        "level": "DEBUG",
        "handlers": [
            "file",
            "rich"
        ]
    }
}
'''

logging.config.dictConfig(json.loads(CONFIG))
