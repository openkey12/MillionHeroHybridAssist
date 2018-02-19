# MillionHeroHybridAssist V5.0
百万英雄、冲顶大会 辅助作答器 使用四引擎+神经网络模型 准确率超高 慎用、侵删！ 2018/02/19 已更新
====
### 新版本提请注意
<b>新年快乐~</b> 新增小白安装包（dist文件夹里是独立安装文件，安装完运行CompaignHelper.exe可以直接运行，专门给普通用户使用的版本，以后长期更新！）<br>新增支持知乎竞答，帮助您赢取更多奖金！<br><br>

### 致谢
* 思路来源：作者`smileboywtu` Repo链接：<link>https://github.com/smileboywtu/MillionHeroAssistant</link> 已于原作者代码有很大不同<br><br>

### 最新战绩
* 2018/02/14 13:00场 12/12 全对，有一题蒙对<br>
* 2018/02/13 13:00场 11/12 错一题（最后一题，仍在调优新算法），仍通关<br>
* 2018/02/12 20:00场 12/12 全部题目均以高解析百分比通过且正确<br><br>

### 工具介绍
本Repo根据其源代码进行了修改和汉化 支持四引擎搜索模式 准确率大幅上升<br>
新增相似度搜寻算法，优化结果表现！<br>
![V4版本运行截图](https://github.com/leyuwei/MillionHeroHybridAssist/blob/master/demoV4.JPG)<br>
使用时，请按照原作者`smileboywtu`的Repo说明进行配置，在此不再赘述。<br>
本Repo大幅提升了相关性能，汉化加强并集成了ADB<br><br>

### 免责声明
<b>代码仅供技术交流使用，切勿用于任何其它用途！用于任何盈利用途后果自负！</b><br>
如有对西瓜视频、冲顶大会等相关利益方的侵权，请联系我立即删除。在此致以诚挚感谢！<br><br>

### 使用前须知
* 您在使用时，需要更换config.py中的baiduOCR等秘钥参数（现在的是没法使用的，需要您自行到百度开发者中心去申请OCR的秘钥并替换<link>https://cloud.baidu.com/</link>，具体操作办法百度一下都有）。否则无法使用！<br>
* 您必须在电脑中安装 Python3.5 或以上版本的环境~~并安装requirements.txt文件~~(已包括在runfirst.bat里)<br>
* 同时为了您能够使用正常，请在使用前以~~管理员模式~~正常模式运行runfirst.bat批处理以初始化运行环境<br>
* 以上三项必须严格执行，否则主程序（main.py）肯定是没办法正常运行的<br><br>


### 工作原理/算法介绍
#### 1、<b>传统搜索匹配</b>
对设问Q并发4个引擎进行搜索，匹配3个选项的个数进行统计。目前采用的引擎是百度搜索、百度知道、必应、360SO。遇到否定设问（XXX不是XXX），则先将问题中的否定词语去除，重复上述搜索步骤。接着将统计结果倒序排列，取权重最小的一个。<br>
#### 2、<b>（原创）泄露量检索</b>
一共3个选项一个问题，分别设为A<sub>1</sub>、A<sub>2</sub>、A<sub>3</sub>、Q。<br>
我们先在百度知道引擎中检索如下关键词（Q A<sub>1</sub>）、（Q A<sub>2</sub>）、（Q A<sub>3</sub>），分别取得三次检索页面中A<sub>1</sub>、A<sub>2</sub>、A<sub>3</sub>出现的次数，存放成一个3X3的矩阵，该矩阵的对角线为搜索（Q A<sub>i</sub>）而出现A<sub>i</sub>的次数，<b>矩阵的行</b>为搜索（Q A<sub>i</sub>）而分别出现三个选项的次数，类似的，<b>矩阵的列</b>就代表检索三个关键词而出现选项A<sub>i</sub>的次数。<br>
我们很容易联想到这样的一个情景：问题“<b>南京市的市花是什么？</b>”，选项：“<b>梅花</b>”、“<b>樱花</b>”、“<b>桃花</b>”。那么只要检索关键词中出现了问题“南京市的市花”，那么无论其之后是否带上这三个选项，检索页面中一定会出现“<b>梅花</b>”这一正确选项，我们将这种现象称之为“<b>泄露</b>”。统计泄露次数可以为我们提供更加精确的答案提供帮助。
将上文中3X3的矩阵的对角元置0，再进一步切分成三个列向量，我们这时可以将这三个生成的列向量分别进行 元素加和 或 欧氏距计算。以计算结果大小作为该选项的权重能够更加有效的识别准确选项。<br>
#### 3、<b>PMI文本关联算法</b>
这在很多辅助答题器中都出现过。即搜索(Q A<sub>1</sub>)、Q、A<sub>1</sub>在百度引擎中的搜索结果数量。通过PMI计算公式：count(Q A<sub>1</sub>)/(count(Q)*count(A<sub>1</sub>))即可算出问题Q与选项A<sub>1</sub>的关联度。<br>
#### 4、<b>（原创）整合模型</b>
将上述三个算法进行整合，有很多思路。本Python脚本采用的只是思路之一，仅供各位参考。相信还有更多优秀的算法等待挖掘。<br>
1、考虑 PMI结果的差值往往是数量级上的差别，而1、2节介绍的算法则仅为个位数的差距，如果我们使用简单的乘法将三个算法相乘，那么结果必将直接取决于PMI算法，这显然不是很合理；<br>
2、我们希望能够在任何一个算法变得不靠谱的时候，将判决结果更多地依赖于剩余的算法（当然，如果三个结果都不靠谱的话，这题只能随缘了~）经过我自己收集的题目测试集的测试，将模型设计如下（设上文三个算法对选项A<sub>i</sub>的计算结果分别为S<sub>1</sub>、S<sub>2</sub>、S<sub>3</sub>）：S = S<sub>3</sub> * ( S<sub>1</sub> * 10 + 1 ) * ( S<sub>2</sub> + 10 )<br>
3、上述模型中,括号中的+1是为了防止各算法结果输出为0的情况，保证1是各个算法输出的最小值。对S<sub>1</sub>乘上10是为了使其权重值增加，S<sub>2</sub>没有乘上该权重因子是因为在测试集表现中，不加会更好，当然上述结论都有待商榷。由于没有足够的数据，故暂时也确实没有办法测试模型的泛化性能。<br>
#### 5、<b>（原创）神经网络模型</b>
使用以往做题的数据训练了传统三层神经网络，隐藏节点数42，epoch=8000，LOSS≈0.8，batch-size有点小，有待后续累积。<br>
在此分为正常题和否定题两个模型进行分别训练，得出训练集上的精度—— 正常题96% 否定题97%。 稍微有一些过拟合，有待后续的参数调优<br><br>

### 更新日志
#### ====  已更新 2018/02/19  ====<br>
* 1、新增小白用户安装包，不依赖任何环境，点点鼠标就运行！
* 2、新增知乎竞答支持<br>

#### ====  已更新 2018/02/15  ====<br>
* 1、修复了当OCR识别不完整时可能出现的种种错误
* 2、优化了界面表现
* 3、新增神经网络算法！<br>

#### ====  已更新 2018/02/13  ====<br>
* 1、新增PMI关联度算法（每次搜索均有不同，和相似度算法结合到一起，模型仍待调整）
* 2、新增可靠度阈值判别（方差>0.71设为答案可信）<br>

#### ====  已更新 2018/02/12  ====<br>
* 1、新增360搜索
* 2、新增语音播报 
* 3、新增百度知道知识树 
* 4、新增浏览器辅助开关
* 5、全新相似算法升级，识别度更高（仍有不足）<br>

#### ====  已更新 2018/02/11  ====<br>
* 1、图像预增强以提升识别准确率
* 2、修正提问问题的判断
* 3、修正正则过滤表达式
* 4、优化结果显示效果
* 5、新增选项预分词处理步骤
* 6、(测试)全新匹配算法<br>

#### ====  已更新 2018/02/08  ====<br>
* 1、加强的否认模式搜索
* 2、新增知乎搜索模式
* 3、新增对iOS设备的支持！期待已久！<br>

#### ====  已更新 2018/02/02  ====<br>
* 1、将所有中文数字转换成阿拉伯数字
* 2、对于题目中携带“未”“没有”"无"的，新增否定题目模式搜索
* 3、双引擎搜索转并发线程
* 4、对于答案中含题目中关键字的，给予足够提示
* 5、搜索的时候，关键字去除前面的题目序号
* 6、对于两个答案权重接近时，同样给出不可靠提示<br>
