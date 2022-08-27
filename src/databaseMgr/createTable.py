import sqlite3

# データベース作成
# すでに存在するなら無視
dbname = '.\\dst\\netkeibaDB\\netkeiba.db'
conn = sqlite3.connect(dbname)

# sqliteを操作するカーソルオブジェクトを作成
cur = conn.cursor()

# horse_prof テーブル作成
# horse_id(PRIMARY KEY), "生年月日", "調教師", "馬主", "生産者", "産地", セリ取引価格, 獲得賞金, "通算成績", "主な勝鞍", "近親馬", "父", "父父", "父母", "母", "母父", "母母", 欠落フラグ
# 例:('1982101018', '1982年4月22日', '00340', '辻幸雄', '谷岡正次', '静内町', '-', 103,300,000, '15戦8勝 [8-3-1-3]', "86'札幌記念(G3)", 'ダンツウイッチ、フォースタテヤマ', 0)
cur.execute('CREATE TABLE horse_prof(horse_id PRIMARY KEY, bod, trainer, owner, producer, area, auction_price, earned, lifetime_record, main_winner, relative, blood_f, blood_ff, blood_fm, blood_m, blood_mf, blood_mm, check_flg)')

# race_info テーブル作成
# horseID(PRIMARY KEY), raceID(PRIMARY KEY), "日付", "開催", 頭数, 枠番, 馬番, オッズ, 人気, 着順, 騎手id, 斤量, "距離", "馬場", "タイム", 着差, 賞金, レースグレード
# 例:('1982101018', '198701010209', '1987/06/14', '1札幌2', 13, 1, 1, 1.4, 1, 1, '00540', 59, 'ダ1800', '良', '1:50.8', -0.2, 1,600.0)
cur.execute('CREATE TABLE race_info(horse_id, race_id, date, venue, horse_num, post_position, horse_number, odds, fav, result, jockey_id, burden_weight, distance, course_condition, time, margin, prize, grade, PRIMARY KEY(horse_id, race_id))')

# race_result テーブル作成
# [horseID,固定[raceID, race_name, race_data1, race_data2,]  goal_time, goal_dif, horse_weight, money]
# horseID(PRIMARY KEY), raceID(PRIMARY KEY), "レース名", "レース情報1", "レース情報2", "タイム", 着差, "馬体重", 賞金
# 例:('1982101018', '198701010209', '第22回札幌記念(G3)', 'ダ右2000m / 天候 : 曇 / ダート : 良 / 発走 : 15:50', 1986年6月29日 1回札幌8日目 4歳以上オープン  (混)(ハンデ)', '2:02.3', 5, '506(+12)', 2,700.0)
cur.execute('CREATE TABLE race_result(horse_id, race_id, race_name, race_data1, race_data2, time, margin, horse_weight, prize, PRIMARY KEY(horse_id, race_id))')

# 変更反映
conn.commit()

# データベースへのコネクションを閉じる
cur.close()
conn.close()
