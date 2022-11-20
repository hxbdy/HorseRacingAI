from Encoder_X import XClass
from getFromDB import db_race_list_horse_id, db_horse_list_parent

import logging
logger = logging.getLogger("UmamusumeClass")

class UmamusumeClass(XClass):

    def get(self):
        # 出馬リストを取得
        horse_list = db_race_list_horse_id(self.race_id)
        self.xList = horse_list

    def fix(self):
        # ウマ娘ちゃんテーブル
        umamusumeTbl = [
            "1995103211", #スペシャルウィーク
            "1994103997", #サイレンススズカ
            "1988101025", #トウカイテイオー
            "000a0003bd", #マルゼンスキー
            "1992109618", #フジキセキ
            "1985102167", #オグリキャップ
            "2009102739", #ゴールドシップ
            "2004104258", #ウオッカ
            "2004103198", #ダイワスカーレット
            "1994109686", #タイキシャトル
            "1995108676", #グラスワンダー
            "1991109852", #ヒシアマゾン
            "1987107235", #メジロマックイーン
            "1995108742", #エルコンドルパサー
            "1996100292", #テイエムオペラオー
            "1991108889", #ナリタブライアン
            "1981107017", #シンボリルドルフ
            "1993109154", #エアグルーヴ
            "1997110025", #アグネスデジタル
            "1995107393", #セイウンスカイ
            "1984101673", #タマモクロス
            "1999110187", #ファインモーション
            "1990103355", #ビワハヤヒデ
            "1992102988", #マヤノトップガン
            "1998101554", #マンハッタンカフェ
            "1989103049", #ミホノブルボン
            "1987105368", #メジロライアン
            "1992110167", #ヒシアケボノ
            "1990103565", #ユキノビジン
            "1989107699", #ライスシャワー
            "1987100579", #アイネスフウジン
            "1998101516", #アグネスタキオン
            "1996107396", #アドマイヤベガ
            "1984106229", #イナリワン
            "1990102314", #ウイニングチケット
            "1997103398", #エアシャカール
            "2007102951", #エイシンフラッシュ
            "2007102807", #カレンチャン
            "2003107045", #カワカミプリンセス
            "1984105823", #ゴールドシチー
            "1989108341", #サクラバクシンオー
            "1994109364", #シーキングザパール
            "1993106964", #シンコウウインディ
            "2001104313", #スイープトウショウ
            "1985104409", #スーパークリーク
            "2005100097", #スマートファルコン
            "2000101517", #ゼンノロブロイ
            "2006103169", #トーセンジョーダン
            "2006102424", #ナカヤマフェスタ
            "1990102766", #ナリタタイシン
            "1989107262", #ニシノフラワー
            "1996106177", #ハルウララ
            "1985104122", #バンブーメモリー
            "1991109886", #ビコーペガサス
            "1992103687", #マーベラスサンデー
            "1994100530", #マチカネフクキタル
            "1980107022", #ミスターシービー
            "1996110113", #メイショウドトウ
            "1994108393", #メジロドーベル
            "1988104866", #ナイスネイチャ
            "1995104427", #キングヘイロー
            "1989103489", #マチカネタンホイザ
            "1987104784", #イクノディクタス
            "1987105372", #メジロパーマー
            "1987102798", #ダイタクヘリオス
            "1988106332", #ツインターボ
            "2013106101", #サトノダイヤモンド
            "2012102013", #キタサンブラック
            "1985100743", #サクラチヨノオー
            "1982103448", #シリウスシンボリ
            "1985103406", #メジロアルダン
            "1985104215", #ヤエノムテキ
            "1995108246", #ツルマルツヨシ
            "1994108411", #メジロブライト
            "2017100720", #デアリングタクト
            "1991103498", #サクラローレル
            "1996102442", #ナリタトップロード
            "1988101069", #ヤマニンゼファー
            "1999110099", #シンボリクリスエス
            "1999100226", #タニノギムレット
            "1987100260", #ダイイチルビー
            "2004103323", #アストンマーチャン
            "1988107943", #ケイエスミラクル
            "2010106548", #コパノリッキー
            "2009100921", #ホッコータルマエ
            "2006106794", #ワンダーアキュート
        ]

        # 親にウマ娘ちゃんがいるか確認
        # 居た場合 1 にする
        umamusume_family = [0] * len(umamusumeTbl)
        horse_list = self.xList
        for i in range(len(horse_list)):
            # horse_list[i] の親にウマ娘ちゃんがいたら umamusume_family[i] = 1 とする
            # 親を取得
            parent_list = db_horse_list_parent(horse_list[i])
            # 親1頭ずつ確認する
            for parent in parent_list:
                # ウマ娘ちゃんならフラグをセットする
                for j in range(len(umamusumeTbl)):
                    if parent == umamusumeTbl[j]:
                        umamusume_family[j] = 1
                        # logger.debug("parent has umamusume : {0}".format(umamusumeTbl[j]))
        self.xList = umamusume_family

    def pad(self):
        pass
    