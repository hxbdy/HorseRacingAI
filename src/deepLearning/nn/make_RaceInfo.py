from RaceInfo import RaceInfo
import encoder
import getFromDB

# horse_number別で実装

# encoder内のclass名とRaceInfoクラスのメンバー名の対応
class_var_dict = {"HorseNum": "horse_num", "RaceStartTime": "start_time", "CourseDistance": "distance",\
    "Weather": "weather", "CourseCondition": "course_condition", "Money": "prize",\
        "PostPosition": "post_position", "BurdenWeight": "burden_weight", "BradleyTerry": "horse_id",\
            "Jockey": "jockey_id"}

# 関数にlocal情報を渡す
local_dict = locals()


def raceinfo_by_raceID(race_id: str):
    """指定レースのRaceInfoオブジェクトをデータベースから作成する
    raceID: レースの指定
    """
    raceInfo = RaceInfo()
    
    raceInfo.race_id = race_id
    raceInfo.date = getFromDB.db_race_date(race_id)
    
    dict_key = list(class_var_dict.keys())
    for name in dict_key:
        file_module = local_dict["encoder"]
        class_module = getattr(file_module, "Encoder_" + name)
        class_obj = getattr(class_module, name + "Class")
        class_obj.set(class_obj, race_id)
        class_obj.get(class_obj)
        setattr(raceInfo, class_var_dict[name], class_obj.xList)

    # 馬番
    raceInfo.horse_number = list(range(1, len(raceInfo.post_position)+1))

    return raceInfo
