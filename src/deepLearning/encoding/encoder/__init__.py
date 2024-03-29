# encoder パッケージ
# 公式:
# 4 PEP 328: Absolute and Relative Imports
# https://docs.python.org/2.5/whatsnew/pep-328.html
# 参考:
# python - relative import from __init__.py file throws error - Stack Overflow
# https://stackoverflow.com/questions/22942650/relative-import-from-init-py-file-throws-error

# 各エンコーダの親
from . import Encoder_X

# 各種エンコーダ
# エンコーダ追加時は以下に追記
from . import Encoder_BradleyTerry
from . import Encoder_BurdenWeight
from . import Encoder_CourseCondition
from . import Encoder_CourseDistance
from . import Encoder_CumPerform
from . import Encoder_HorseAge
from . import Encoder_HorseNum
from . import Encoder_Jockey
from . import Encoder_Money
from . import Encoder_FatherBradleyTerry
from . import Encoder_MotherBradleyTerry
from . import Encoder_PostPosition
from . import Encoder_RaceStartTime
from . import Encoder_Umamusume
from . import Encoder_Weather
from . import Encoder_Last3f
from . import Encoder_HorseWeight
from . import Encoder_CornerPos
from . import Encoder_Pace
from . import Encoder_Review
from . import Encoder_LastRaceLeft
from . import Encoder_JockeyBradleyTerry

# 正解ラベル用
from . import Encoder_Margin
from . import Encoder_RankOneHot
from . import Encoder_Time
