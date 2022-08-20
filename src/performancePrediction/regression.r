# -*- coding: utf-8 -*-
# 3着馬の走破タイムを予想するLMEモデルの係数を計算
# 注) カレントディレクトリをこのスクリプトがあるディレクトリに移動すること

# lme4をインストールしていない場合はinstall.packages("lme4")でインストールする
library(lme4)

# データの読み込み
d1 <- read.csv("dataSet.csv", header=TRUE)

# 計算
mixedModel <- lmer(goaltime ~ dist + (1|cond) + (1|track) + (1|loc), d1)
a <- fixef(mixedModel)
r <- ranef(mixedModel)

write.csv(x=a, file="fixedEffect_coef.csv")
write.csv(x=b, file="randomEffect_coef.csv")
