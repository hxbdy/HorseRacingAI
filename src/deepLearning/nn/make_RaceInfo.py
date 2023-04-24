from RaceInfo      import RaceInfo
from NetkeibaDB_IF import NetkeibaDB_IF

def raceinfo_by_raceID(race_id: str):
    """指定レースのRaceInfoオブジェクトをデータベースから作成する
    raceID: レースの指定
    """
    raceInfo = RaceInfo()
    nf = NetkeibaDB_IF("ROM")
    
    raceInfo.race_id          = race_id
    raceInfo.date             = nf.db_race_date(race_id)
    raceInfo.horse_num        = nf.db_race_num_horse(race_id)
    raceInfo.start_time       = nf.db_race_start_time(race_id)
    raceInfo.distance         = [nf.db_race_distance(race_id)]
    raceInfo.weather          = nf.db_race_weather(race_id)
    raceInfo.course_condition = nf.db_race_cource_condition(race_id)
    raceInfo.prize            = nf.db_race_list_prize(race_id)
    raceInfo.post_position    = nf.db_race_list_post_position(race_id)
    raceInfo.horse_number     = list(range(1, len(raceInfo.post_position)+1))
    raceInfo.burden_weight    = nf.db_race_list_burden_weight(race_id)
    raceInfo.horse_weight     = nf.db_race_horse_weight(race_id)
    raceInfo.horse_id         = nf.db_race_list_horse_id(race_id)
    raceInfo.jockey_id        = nf.db_race_list_jockey(race_id)

    return raceInfo
