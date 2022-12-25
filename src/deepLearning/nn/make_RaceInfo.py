from RaceInfo import RaceInfo
from encoder import *
import getFromDB

# horse_number別で実装

# 利用するEncoderクラス名
classList = ["HorseNum", "RaceStartTime", "CourseDistance", "Weather",\
    "CourseCondition", "Money", "PostPosition", "BurdenWeight",\
        "BradleyTerry", "Jockey"]
# RaceInfoクラスの変数名
varList = ["horse_num", "start_time", "distance", "weather",\
    "course_condition", "prize", "post_position", "burden_weight",\
        "horse_id", "jockey_id"]

# 関数にlocal情報を渡す
local_dict = locals()


def raceinfo_by_raceID(race_id: str):
    """指定レースのRaceInfoオブジェクトをデータベースから作成する
    raceID: レースの指定
    """
    raceInfo = RaceInfo()
    
    raceInfo.race_id = race_id
    raceInfo.date = getFromDB.db_race_date(race_id)
    
    for i in range(len(classList)):
        name = classList[i]
        module = local_dict["Encoder_" + name]
        class_obj = getattr(module, name + "Class")
        class_obj.set(class_obj, race_id)
        class_obj.get(class_obj)
        setattr(raceInfo, varList[i], class_obj.xList)

    # 馬番
    raceInfo.horse_number = list(range(1, len(raceInfo.post_position)+1))

    # TODO: predictHorseNumClassを調整してこの処理は削除したい
    raceInfo.horse_num = raceInfo.horse_num[0]

    return raceInfo
