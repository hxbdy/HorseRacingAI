# DB に問い合わせ、取得したデータを整形する
# どこでデータ整形しているのかがわからなくなるため
# ここで行って良い変換処理はDBから取得したデータの変換のみ
# エンコードに都合の良いように変換する作業は各クラスのget, fixで行う

from datetime import date

from NetkeibaDB import NetkeibaDB
from debug import *

# load DB
config = configparser.ConfigParser()
config.read('./src/path.ini', 'UTF-8')
path_netkeibaDB = config.get('common', 'path_netkeibaDB')
netkeibaDB = NetkeibaDB(path_netkeibaDB)

def db_race_1st_odds(race_id):
    # 指定レースの1位オッズをfloatで返す
    odds = netkeibaDB.sql_mul_tbl("race_info", ["odds"], ["race_id", "result"], [race_id, "1"])
    return float(odds[0])

def db_race_list_id(start_year = 0, end_year = 9999, limit = -1):
    # yearを含む年のレースまでをlimit件取得する
    # limit を指定しない場合は全件検索
    # デフォルトでは全てのレースを取得する
    # DB上のrace_idの上4桁は開催年前提
    if len(str(start_year)) != 4:
        logger.critical("len(str(start_year)) != 4")
        start_year = "0000"
    if len(str(end_year)) != 4:
        logger.critical("len(str(end_year)) != 4")
        end_year = "9999"
    start_year = str(start_year) + "00000000"
    end_year   = str(end_year)   + "99999999"

    if limit <= 0:
        # 全件検索
        # SQLite Int の最大値 2**63 -1
        limit = 9223372036854775807

    totalRaceList = netkeibaDB.sql_mul_distinctColCnt_G1G2G3(start_year, end_year, limit)
    return totalRaceList

def db_race_date(race_id):
    # レース開催日を取り出す
    # 以下の前提で計算する
    # race_data2 にレース開催日が含まれていること
    raceDate = netkeibaDB.sql_mul_tbl("race_result", ["race_data2"], ["race_id"], [race_id])
    raceDate = raceDate[0]
    raceDateYear = int(raceDate.split("年")[0])
    raceDateMon = int(raceDate.split("年")[1].split("月")[0])
    raceDateDay = int(raceDate.split("月")[1].split("日")[0])
    return date(raceDateYear, raceDateMon, raceDateDay)

def db_race_grade(race_id):
    # レースのグレードを返す
    # 不明の場合-1を返す
    raceGrade = netkeibaDB.sql_mul_tbl("race_info", ["grade"], ["race_id"], [race_id])
    return int(raceGrade[0])

def db_race_list_prize(race_id):
    # レースの賞金をリストで返す
    # (降順ソートされているか未確認)
    prizeList = netkeibaDB.sql_mul_tbl("race_result", ["prize"], ["race_id"], [race_id])
    for i in range(len(prizeList)):
        prizeList[i] = str(prizeList[i])
    return prizeList

def db_race_num_horse(race_id):
    # 出走する頭数を返す
    return [netkeibaDB.sql_one_rowCnt("race_result", "race_id", race_id)]

def db_race_list_race_data1(race_id):
    # race_result テーブルの race_data1 列のデータを取得する
    return netkeibaDB.sql_mul_tbl("race_result", ["race_data1"], ["race_id"], [race_id])

def db_race_list_horse_id(race_id):
    # 馬番でソートされた出走する馬のIDリストを返す
    return netkeibaDB.sql_mul_sortHorseNum(["race_info.horse_id"], "race_info.race_id", race_id)

def db_horse_bod(horse_id):
    # 馬の誕生日を返す
    data = netkeibaDB.sql_one_horse_prof(horse_id, "bod")
    birthYear = int(data.split("年")[0])
    birthMon = int(data.split("年")[1].split("月")[0])
    birthDay = int(data.split("月")[1].split("日")[0])
    return date(birthYear, birthMon, birthDay)

def db_race_list_burden_weight(race_id):
    # 斤量リストをfloatに変換して返す
    burdenWeightList = netkeibaDB.sql_mul_sortHorseNum(["race_info.burden_weight"], "race_info.race_id", race_id)
    for i in range(len(burdenWeightList)):
        burdenWeightList[i] = float(burdenWeightList[i])
    return burdenWeightList

def db_race_list_post_position(race_id):
    # 枠番リストをfloatに変換して返す
    postPositionList = netkeibaDB.sql_mul_sortHorseNum(["race_info.post_position"], "race_info.race_id", race_id)
    for i in range(len(postPositionList)):
        postPositionList[i] = float(postPositionList[i])
    return postPositionList

def db_race_list_jockey(race_id):
    # 騎手リストを返す
    jockeyIDList = netkeibaDB.sql_mul_sortHorseNum(["race_info.jockey_id"], "race_info.race_id", race_id)
    for i in range(len(jockeyIDList)):
        jockeyIDList[i] = str(jockeyIDList[i])
    return jockeyIDList

def db_race_cnt_jockey(jockey_id):
    # 騎手の総出場回数を求める
    return netkeibaDB.sql_one_rowCnt("race_info", "jockey_id", jockey_id)

def db_horse_list_parent(horse_id):
    # 親馬のIDリストを返す
    parent_list = netkeibaDB.sql_mul_tbl("horse_prof", ["blood_f", "blood_ff", "blood_fm", "blood_m", "blood_mf", "blood_mm"], ["horse_id"], [horse_id])
    parent_list = parent_list[0]
    return parent_list

def db_horse_list_perform(horse_id):
    # パフォーマンス計算に必要な列を返す
    col = ["horse_id", "venue", "time", "burden_weight", "course_condition", "distance", "grade"]
    race = netkeibaDB.sql_mul_tbl("race_info", col, ["horse_id"], [horse_id])
    return race

def db_race_list_margin(race_id):
    # 着差を文字列のリストで返す
    marginList = netkeibaDB.sql_mul_tbl("race_result", ["margin"], ["race_id"], [race_id])
    for i in range(len(marginList)):
        marginList[i] = str(marginList[i])

def db_race_rank(race_id, horse_id):
    # race_id で horse_id は何位だったか取得
    return netkeibaDB.sql_one_race_info(race_id, horse_id, "result")

def db_race_list_1v1(horse_id_1, horse_id_2):
    # horse_id_1, horse_id_2 が出走したレースリストを返す
    return netkeibaDB.sql_mul_race_id_1v1(horse_id_1, horse_id_2)

def db_horse_father(horse_id):
    # 父のidを返す
    return netkeibaDB.sql_one_horse_prof(horse_id, "blood_f")

def db_race_list_rank(race_id):
    # 馬番で昇順ソートされた順位を文字列で返す
    rankList = netkeibaDB.sql_mul_sortHorseNum(["race_info.result"], "race_info.race_id", race_id)
    for i in range(len(rankList)):
        rankList[i] = str(rankList[i])
    return rankList

def db_race_last_3f(race_id, horse_id):
    # 上がり3ハロンを返す
    last_3f = netkeibaDB.sql_one_race_info(race_id, horse_id, "last_3f")
    return last_3f

def db_race_last_race(race_id, horse_id):
    # horse_id が出走した重賞レースのうち、race_idの直前に走ったレースIDを返す
    # 見つからなかった場合、出走レース一覧から一番最近のrace_idを返す
    # 指定のrace_idより古いレースがない場合は指定のrace_idをそのまま返す

    # これは直前の調子をはかるために使う
    # 直前のレースが重賞以外のとき、現状は重賞まで遡ってタイムを取得している。
    # が、直前のレースのグレードは関係ないと思う。ラスト3ハロンタイムは
    # TODO: グレードに関係なく取得したほうがいいのでは...?

    # horse_idの重賞出走レース一覧を取得する
    race_list = netkeibaDB.sql_mul_tbl_g1g2g3("race_result", ["race_id"], ["horse_id"], [horse_id])
    # 昇順ソート
    race_list.sort()

    # 直前の重賞レースIDを返す
    if race_id in race_list:
        last_race_id = race_list.index(race_id) - 1
        if(last_race_id < 0):
            # race_id が一番古い重賞レースだった
            # race_id をそのまま返す
            return race_id
        else:
            # race_id の直前の race_id が見つかった
            return race_list[last_race_id]
    else:
        # predict 時にはここを通過する (DBには無いレースを走るため)
        # race_id がなかった場合、最新のrace_idを返す
        return race_list[-1]
