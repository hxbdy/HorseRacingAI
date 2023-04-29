

from Encoder_BradleyTerry import BradleyTerryClass

class FatherBradleyTerryClass(BradleyTerryClass):
    def get(self):
        childList = self.nf.db_race_list_horse_id(self.race_id)
        parentList = []
        for i in range(len(childList)):
            # 父のidを取得
            parent = self.nf.db_horse_parent(childList[i], 'f')
            parentList.append(parent)
        self.xList = parentList
        self.col_num = len(self.xList)
