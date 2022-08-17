# 損失関数を二乗和誤差にすることについて
softmax($a$) $\longrightarrow$ CEE($y$) $\longrightarrow$ $L$
## 二乗和誤差(SSE)
$$SSE(y, x) = \frac{ 1 }{ 2 }\lbrace (y_1-t_1)^2 + (y_2-t_2)^2 + (y_3-t_3)^2 \rbrace$$
$$\frac{ \partial SSE }{ \partial y_1 } = y_1 - t_1$$
## softmax
$$\frac{ \partial f }{ \partial a_1 } = \left [\left (\frac{y_1-t_1}{S}\right )+\left\lbrace-\frac{1}{S^2}\left(\frac{{e^{a_1^2}}}{S}-t_1e^{a_1}\right)\right\rbrace \right]e^{a_1}$$

$y_1 = \frac{e^{a_1}}{S}$より$\frac{{e^{a_1^2}}}{S}=\frac{{e^{a_1^2}}}{S^2}S=y^2_1S$

$$= \left [\frac{y_1-t_1}{S}+\left\lbrace-\frac{1}{S^2}\left(y^2_1S-t_1e^{a_1}\right)\right\rbrace\right] e^{a_1}$$

$$=\left(\frac{y_1-t_1}{S}-\frac{y^2_1}{S}+\frac{t_1y_1}{S}\right)e^{a_1}$$

$$=\frac{e^{a_1}}{S}(y_1-t_1-y^2_1+t_1y_1)$$

$$=y_1(-y^2_1+y_1+t_1y_1-t_1)$$

$$=-y_1\lbrace y_1(y_1-1)-t_1(y_1-1)\rbrace$$

$$=-y_1(y_1-1)(y_1-t_1)$$