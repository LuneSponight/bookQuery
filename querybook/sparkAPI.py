
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("SparkJDBC").master("spark://master:7077").getOrCreate()
sc = spark.sparkContext
sc.addPyFile('qureybook/help.py')

import help
url = "jdbc:mysql://192.168.10.1:3306/bookquery"
properties = {"user": "root", "password": "mysQlSSnig449*"}


Author = spark.read.jdbc(url=url, table="Author", properties=properties)
Novel = spark.read.jdbc(url=url, table="Novel", properties=properties)
Category = spark.read.jdbc(url=url, table="Category", properties=properties)
Tag = spark.read.jdbc(url=url, table="Tag", properties=properties)
NovelTag = spark.read.jdbc(url=url, table="NovelTag", properties=properties)


def CalculateHeatDegree(NovelID_List):
    Top10Heat_Novel_MonthlyClicks = Novel.select(Novel["NovelID"], Novel["Title"], Novel["MonthlyClicks"]).rdd \
        .filter(lambda x: x[0] in NovelID_List).map(lambda x: (x[1], int(x[2]))).sortBy(keyfunc=lambda x: x[1],
                                                                                        ascending=False).take(10)
    RecommendNovelList = []
    RecommendNovelClicksList = []
    for k, v in Top10Heat_Novel_MonthlyClicks:
        RecommendNovelList.append(k)
        RecommendNovelClicksList.append(v)
    return RecommendNovelList, RecommendNovelClicksList


def StatisticsByCount(Params_list):
    Return_Dict = {}
    # 判断筛选条件是否有效
    Valid_list = [Params_list[1] == [], Params_list[2] == [], Params_list[0] == []]

    Select_Category = Params_list[0]
    Select_Category = help.MapIndexToCorCategory(Select_Category)

    Select_Tag = Params_list[1]
    Select_Tag = help.MapIndexToCorTag(Select_Tag)

    Select_Author = Params_list[2]

    Select_CategoryID_list = Category.rdd.map(lambda x: (x[0], x[1])).filter(lambda x: x[1] in Select_Category).map(
        lambda x: x[0]).collect()

    Select_TagID_list = Tag.rdd.filter(lambda x: x[1] in Select_Tag).map(lambda x: x[0]).collect()
    Select_NovelID_list_BasedOnTagID = NovelTag.select(NovelTag["NovelID"], NovelTag["TagID"]).rdd.filter(
        lambda x: x[1] in Select_TagID_list).map(lambda x: x[0]).collect()

    Select_AuthorID_list = Author.rdd.filter(lambda x: x[1] in Select_Author).map(lambda x: x[0]).collect()

    Select_list = [Select_NovelID_list_BasedOnTagID, Select_AuthorID_list, Select_CategoryID_list]

    # 根据三个条件筛选出对应的NovelID列表
    Select_NovelID_list_ByThree = \
        Novel.select(Novel["NovelID"], Novel["AuthorID"], Novel["CategoryID"]) \
            .rdd.filter(lambda x: help.JudgeByThree(x, Select_list, Valid_list)) \
            .map(lambda x: x[0]).collect()

    Select_Novel_Number = len(Select_NovelID_list_ByThree)
    temdict = {}
    temdict["name"] = "总计数量"
    temdict["value"] = Select_Novel_Number
    Return_Dict["总计"] = [temdict]

    # 在选出的小说根据月点击量进行分类并计算每个类别的小说数量
    NumclassifiedbyClicks = Novel.select(Novel['NovelID'], Novel['MonthlyClicks']).rdd.filter(
        lambda x: x[0] in Select_NovelID_list_ByThree).keyBy(lambda x: help.AddMonthlyClicksKey(x)).countByKey()
    Return_Dict["点击量"] = help.ConvertMyDictToNeedDict(dict(NumclassifiedbyClicks))

    # 在选出的小说根据月推荐票进行分类并计算每个类别的小说数量
    NumclassifiedbyMonrecoms = Novel.select(Novel['NovelID'], Novel['MonthlyRecommendations']).rdd.filter(
        lambda x: x[0] in Select_NovelID_list_ByThree).keyBy(
        lambda x: help.AddMonthlyRecommendationsKey(x)).countByKey()

    # 在选出的小说根据读者数量进行分类并计算每个类别的小说数量
    NumclassifiedbyReaderCount = Novel.select(Novel['NovelID'], Novel['ReaderCount']).rdd.filter(
        lambda x: x[0] in Select_NovelID_list_ByThree).keyBy(lambda x: help.AddReaderCountKey(x)).countByKey()
    Return_Dict["读者数量"] = help.ConvertMyDictToNeedDict(dict(NumclassifiedbyReaderCount))

    # 在选出的小说根据小说字数进行分类并计算每个类别的小说数量
    NumclassifiedbyWordCount = Novel.select(Novel['NovelID'], Novel['WordCount']).rdd.filter(
        lambda x: x[0] in Select_NovelID_list_ByThree).keyBy(lambda x: help.AddWordCountKey(x)).countByKey()
    Return_Dict["小说字数"] = help.ConvertMyDictToNeedDict(dict(NumclassifiedbyWordCount))

    # 在选出的小说根据礼物数量进行分类并计算每个类别的小说数量
    NumclassifiedbyGiftCount = Novel.select(Novel['NovelID'], Novel['GiftCount']).rdd.filter(
        lambda x: x[0] in Select_NovelID_list_ByThree).keyBy(lambda x: help.AddGiftCountKey(x)).countByKey()
    Return_Dict["礼物数量"] = help.ConvertMyDictToNeedDict(dict(NumclassifiedbyGiftCount))

    # 在选出的小说根据总推荐票进行分类并计算每个类别的小说数量
    NumclassifiedbyTotalRecoms = Novel.select(Novel['NovelID'], Novel['TotalRecommendations']).rdd.filter(
        lambda x: x[0] in Select_NovelID_list_ByThree).keyBy(lambda x: help.AddTotalRecommencdationsKey(x)).countByKey()
    Return_Dict["总推荐票"] = help.ConvertMyDictToNeedDict(dict(NumclassifiedbyTotalRecoms))

    # 在选出的小说根据粉丝值进行分类并计算每个类别的小说数量
    NumclassifiedbyTotalFans = Novel.select(Novel['NovelID'], Novel['TotalFans']).rdd.filter(
        lambda x: x[0] in Select_NovelID_list_ByThree).keyBy(lambda x: help.AddTotalFansKey(x)).countByKey()

    # 在选出的小说根据评论数进行分类并计算每个类别的小说数量
    NumclassifiedbyCommentCount = Novel.select(Novel['NovelID'], Novel['CommentCount']).rdd.filter(
        lambda x: x[0] in Select_NovelID_list_ByThree).keyBy(lambda x: help.AddCommentCountKey(x)).countByKey()

    # print(Return_Dict)
    # print(CalculateHeatDegree())

    Return_Dict["barchart_novels"], Return_Dict["barchart_clicks"] = CalculateHeatDegree(Select_NovelID_list_ByThree)
    return Return_Dict


# StatisticsByCount([[0,1],[],[]])
# print()

def StatisticsByCategory(Params_list):
    Return_Dict = {}
    # 判断筛选条件是否有效
    Valid_list = [Params_list[1] == [], Params_list[2] == [], Params_list[0] == []]

    Select_Category = Params_list[0]
    Select_Category = help.MapIndexToCorCategory(Select_Category)

    Select_Tag = Params_list[1]
    Select_Tag = help.MapIndexToCorTag(Select_Tag)

    Select_Author = Params_list[2]

    Select_CategoryID_list = Category.rdd.map(lambda x: (x[0], x[1])).filter(lambda x: x[1] in Select_Category).map(
        lambda x: x[0]).collect()

    Select_TagID_list = Tag.rdd.filter(lambda x: x[1] in Select_Tag).map(lambda x: x[0]).collect()
    Select_NovelID_list_BasedOnTagID = NovelTag.select(NovelTag["NovelID"], NovelTag["TagID"]).rdd.filter(
        lambda x: x[1] in Select_TagID_list).map(lambda x: x[0]).collect()

    Select_AuthorID_list = Author.rdd.filter(lambda x: x[1] in Select_Author).map(lambda x: x[0]).collect()

    Select_list = [Select_NovelID_list_BasedOnTagID, Select_AuthorID_list, Select_CategoryID_list]

    # 根据三个条件筛选出对应的NovelID列表
    Select_NovelID_list_ByThree = \
        Novel.select(Novel["NovelID"], Novel["AuthorID"], Novel["CategoryID"]) \
            .rdd.filter(lambda x: help.JudgeByThree(x, Select_list, Valid_list)) \
            .map(lambda x: x[0]).collect()

    # 在选出的小说中计算不同类别小说的数量
    Select_Novel_CateID_NovlID_CateNa = Novel.select(Novel["CategoryID"], Novel["NovelID"]).rdd.filter(
        lambda x: x[1] in Select_NovelID_list_ByThree).join(Category.rdd)
    Return_Dict["总计"] = help.ConvertMyDictToNeedDict(
        dict(Select_Novel_CateID_NovlID_CateNa.map(lambda x: (x[1][1], x[1][0])).countByKey()))

    # 在选出的小说中计算不同类别小说的平均月点击量
    Select_Novel_CateName_MonthlyClicks = Novel.select(Novel["CategoryID"], Novel["NovelID"],
                                                       Novel["MonthlyClicks"]).rdd.filter(
        lambda x: x[1] in Select_NovelID_list_ByThree) \
        .map(lambda x: (x[0], (x[1], x[2]))).join(Category.rdd).map(lambda x: (x[1][1], int(x[1][0][1])))
    Return_Dict["点击量"] = help.ConvertMyDictToNeedDict(
        dict(help.CalculateMeanByDiffClass(Select_Novel_CateName_MonthlyClicks).collect()))

    # 在选出的小说中计算不同类别小说的平均月推荐票
    Select_Novel_CateName_MonthlyRecommendations = Novel.select(Novel["CategoryID"], Novel["NovelID"],
                                                                Novel["MonthlyRecommendations"]).rdd.filter(
        lambda x: x[1] in Select_NovelID_list_ByThree) \
        .map(lambda x: (x[0], (x[1], x[2]))).join(Category.rdd).map(lambda x: (x[1][1], int(x[1][0][1])))

    # 在选出的小说中计算不同类别小说的平均读者数量
    Select_Novel_CateName_ReaderCount = Novel.select(Novel["CategoryID"], Novel["NovelID"],
                                                     Novel["ReaderCount"]).rdd.filter(
        lambda x: x[1] in Select_NovelID_list_ByThree) \
        .map(lambda x: (x[0], (x[1], x[2]))).join(Category.rdd).map(lambda x: (x[1][1], int(x[1][0][1])))
    Return_Dict["读者数量"] = help.ConvertMyDictToNeedDict(
        dict(help.CalculateMeanByDiffClass(Select_Novel_CateName_ReaderCount).collect()))

    # 在选出的小说中计算不同类别小说的平均字数
    Select_Novel_CateName_WordCount = Novel.select(Novel["CategoryID"], Novel["NovelID"],
                                                   Novel["WordCount"]).rdd.filter(
        lambda x: x[1] in Select_NovelID_list_ByThree) \
        .map(lambda x: (x[0], (x[1], x[2]))).join(Category.rdd).map(lambda x: (x[1][1], int(x[1][0][1])))
    Return_Dict["小说字数"] = help.ConvertMyDictToNeedDict(
        dict(help.CalculateMeanByDiffClass(Select_Novel_CateName_WordCount).collect()))

    # 在选出的小说中计算不同类别小说的平均礼物数
    Select_Novel_CateName_GiftCount = Novel.select(Novel["CategoryID"], Novel["NovelID"],
                                                   Novel["GiftCount"]).rdd.filter(
        lambda x: x[1] in Select_NovelID_list_ByThree) \
        .map(lambda x: (x[0], (x[1], x[2]))).join(Category.rdd).map(
        lambda x: (x[1][1], int(help.ConvertToValidStr(x[1][0][1]))))
    Return_Dict["礼物数量"] = help.ConvertMyDictToNeedDict(
        dict(help.CalculateMeanByDiffClass(Select_Novel_CateName_GiftCount).collect()))

    # 在选出的小说中计算不同类别小说的平均总推荐票
    Select_Novel_CateName_TotalRecommendations = Novel.select(Novel["CategoryID"], Novel["NovelID"],
                                                              Novel["TotalRecommendations"]).rdd.filter(
        lambda x: x[1] in Select_NovelID_list_ByThree) \
        .map(lambda x: (x[0], (x[1], x[2]))).join(Category.rdd).map(
        lambda x: (x[1][1], int(help.ConvertToValidStr(x[1][0][1]))))
    Return_Dict["总推荐票"] = help.ConvertMyDictToNeedDict(
        dict(help.CalculateMeanByDiffClass(Select_Novel_CateName_TotalRecommendations).collect()))

    # 在选出的小说中计算不同类别小说的平均粉丝值
    Select_Novel_CateName_TotalFans = Novel.select(Novel["CategoryID"], Novel["NovelID"],
                                                   Novel["TotalFans"]).rdd.filter(
        lambda x: x[1] in Select_NovelID_list_ByThree) \
        .map(lambda x: (x[0], (x[1], x[2]))).join(Category.rdd).map(
        lambda x: (x[1][1], int(help.ConvertToValidStr(x[1][0][1]))))

    # 在选出的小说中计算不同类别小说的平均评论数
    Select_Novel_CateName_CommentCount = Novel.select(Novel["CategoryID"], Novel["NovelID"],
                                                      Novel["CommentCount"]).rdd.filter(
        lambda x: x[1] in Select_NovelID_list_ByThree) \
        .map(lambda x: (x[0], (x[1], x[2]))).join(Category.rdd).map(lambda x: (x[1][1], int(x[1][0][1])))

    # print(Return_Dict)
    # print(CalculateHeatDegree())
    Return_Dict["barchart_novels"], Return_Dict["barchart_clicks"] = CalculateHeatDegree(Select_NovelID_list_ByThree)
    return Return_Dict


# StatisticsByCategory([[0,1],[],[]])
# print()

def StatisticsByTag(Params_list):
    Return_Dict = {}
    # 判断筛选条件是否有效
    Valid_list = [Params_list[1] == [], Params_list[2] == [], Params_list[0] == []]

    Select_Category = Params_list[0]
    Select_Category = help.MapIndexToCorCategory(Select_Category)

    Select_Tag = Params_list[1]
    Select_Tag = help.MapIndexToCorTag(Select_Tag)

    Select_Author = Params_list[2]

    Select_CategoryID_list = Category.rdd.map(lambda x: (x[0], x[1])).filter(lambda x: x[1] in Select_Category).map(
        lambda x: x[0]).collect()

    Select_TagID_list = Tag.rdd.filter(lambda x: x[1] in Select_Tag).map(lambda x: x[0]).collect()
    Select_NovelID_list_BasedOnTagID = NovelTag.select(NovelTag["NovelID"], NovelTag["TagID"]).rdd.filter(
        lambda x: x[1] in Select_TagID_list).map(lambda x: x[0]).collect()

    Select_AuthorID_list = Author.rdd.filter(lambda x: x[1] in Select_Author).map(lambda x: x[0]).collect()

    Select_list = [Select_NovelID_list_BasedOnTagID, Select_AuthorID_list, Select_CategoryID_list]

    # 根据三个条件筛选出对应的NovelID列表
    Select_NovelID_list_ByThree = \
        Novel.select(Novel["NovelID"], Novel["AuthorID"], Novel["CategoryID"]) \
            .rdd.filter(lambda x: help.JudgeByThree(x, Select_list, Valid_list)) \
            .map(lambda x: x[0]).collect()

    # 在选出的小说中中计算不同标签小说的数量
    Select_Novel_TagName_NovelID = NovelTag.select(NovelTag["TagID"], NovelTag["NovelID"]).rdd \
        .filter(lambda x: x[1] in Select_NovelID_list_ByThree).join(Tag.rdd) \
        .map(lambda x: (x[1][1], x[1][0])).filter(lambda x: (x[0] in Select_Tag) or Valid_list[0]).sortBy(
        keyfunc=lambda x: x[1])
    Return_Dict["总计"] = help.ConvertMyDictToNeedDict(dict(Select_Novel_TagName_NovelID.countByKey()))

    # 在选出的小说中计算不同标签小说的平均月点击量
    Select_Novel_TagName_MonthlyClicks = Select_Novel_TagName_NovelID.map(lambda x: (x[1], x[0])) \
        .join(Novel.select(Novel["NovelID"], Novel["MonthlyClicks"]).rdd).map(lambda x: (x[1][0], int(x[1][1])))
    Return_Dict["点击量"] = help.ConvertMyDictToNeedDict(
        dict(help.CalculateMeanByDiffClass(Select_Novel_TagName_MonthlyClicks).collect()))

    # 在选出的小说中计算不同标签小说的平均月推荐票
    Select_Novel_TagName_MonthlyRecommendations = Select_Novel_TagName_NovelID.map(lambda x: (x[1], x[0])) \
        .join(Novel.select(Novel["NovelID"], Novel["MonthlyRecommendations"]).rdd).map(
        lambda x: (x[1][0], int(x[1][1])))

    # 在选出的小说中计算不同标签小说的平均读者数量
    Select_Novel_TagName_ReaderCount = Select_Novel_TagName_NovelID.map(lambda x: (x[1], x[0])) \
        .join(Novel.select(Novel["NovelID"], Novel["ReaderCount"]).rdd).map(lambda x: (x[1][0], int(x[1][1])))
    Return_Dict["读者数量"] = help.ConvertMyDictToNeedDict(
        dict(help.CalculateMeanByDiffClass(Select_Novel_TagName_ReaderCount).collect()))

    # 在选出的小说中计算不同标签小说的平均字数
    Select_Novel_TagName_WordCount = Select_Novel_TagName_NovelID.map(lambda x: (x[1], x[0])) \
        .join(Novel.select(Novel["NovelID"], Novel["WordCount"]).rdd).map(lambda x: (x[1][0], int(x[1][1])))
    Return_Dict["小说字数"] = help.ConvertMyDictToNeedDict(
        dict(help.CalculateMeanByDiffClass(Select_Novel_TagName_WordCount).collect()))

    # 在选出的小说中计算不同标签小说的平均礼物数
    Select_Novel_TagName_GiftCount = Select_Novel_TagName_NovelID.map(lambda x: (x[1], x[0])) \
        .join(Novel.select(Novel["NovelID"], Novel["GiftCount"]).rdd).map(
        lambda x: (x[1][0], int(help.ConvertToValidStr(x[1][1]))))
    Return_Dict["礼物数量"] = help.ConvertMyDictToNeedDict(
        dict(help.CalculateMeanByDiffClass(Select_Novel_TagName_GiftCount).collect()))

    # 在选出的小说中计算不同标签小说的平均总推荐票
    Select_Novel_TagName_TotalRecommendations = Select_Novel_TagName_NovelID.map(lambda x: (x[1], x[0])) \
        .join(Novel.select(Novel["NovelID"], Novel["TotalRecommendations"]).rdd).map(
        lambda x: (x[1][0], int(help.ConvertToValidStr(x[1][1]))))
    Return_Dict["总推荐票"] = help.ConvertMyDictToNeedDict(
        dict(help.CalculateMeanByDiffClass(Select_Novel_TagName_TotalRecommendations).collect()))

    # 在选出的小说中计算不同标签小说的平均粉丝值
    Select_Novel_TagName_TotalFans = Select_Novel_TagName_NovelID.map(lambda x: (x[1], x[0])) \
        .join(Novel.select(Novel["NovelID"], Novel["TotalFans"]).rdd).map(
        lambda x: (x[1][0], int(help.ConvertToValidStr(x[1][1]))))

    # 在选出的小说中计算不同标签小说的平均评论数
    Select_Novel_TagName_CommentCount = Select_Novel_TagName_NovelID.map(lambda x: (x[1], x[0])) \
        .join(Novel.select(Novel["NovelID"], Novel["CommentCount"]).rdd).map(
        lambda x: (x[1][0], int(help.ConvertToValidStr(x[1][1]))))

    # print(Return_Dict)
    # print(CalculateHeatDegree())
    Return_Dict["barchart_novels"], Return_Dict["barchart_clicks"] = CalculateHeatDegree(Select_NovelID_list_ByThree)
    return Return_Dict


# StatisticsByTag([[],[0,1],[]])
# print()

def RecommendaByReadNovel(NovelName):
    ReadNovel = Novel \
        .select(Novel["NovelID"], Novel["Title"], Novel["AuthorID"], Novel["CategoryID"]).rdd \
        .filter(lambda x: x[1] == NovelName).collect()
    if (ReadNovel == []):
        print("找不到该小说的信息")
        return
    ReadNovel_NovelID, ReadNovel_AuthorID, ReadNovel_CategoryID = ReadNovel[0][0], ReadNovel[0][2], ReadNovel[0][3]

    SameAuthorNovelList = Novel.select(Novel["AuthorID"], Novel["Title"]).rdd \
        .filter(lambda x: x[0] == ReadNovel_AuthorID and x[1] != NovelName).map(lambda x: x[1]).collect()
    print("该书作者的其他小说:", SameAuthorNovelList)

    SameCategoryNovelList = Novel.select(Novel["CategoryID"], Novel["Title"], Novel["MonthlyClicks"]). \
        rdd.filter(lambda x: x[0] == ReadNovel_CategoryID and x[1] != NovelName).map(lambda x: (x[1], int(x[2]))) \
        .sortBy(keyfunc=lambda x: x[1], ascending=False).map(lambda x: x[0]).take(10)
    print("同一分类的其他小说中热度最高的10本小说:", SameCategoryNovelList)

    ReadNovel_TagIDList = NovelTag.select(NovelTag["NovelID"], NovelTag["TagID"]).rdd. \
        filter(lambda x: x[0] == ReadNovel_NovelID).map(lambda x: x[1]).collect()
    SameTagNovel_NovelIDList = NovelTag.select(NovelTag["NovelID"], NovelTag["TagID"]). \
        rdd.filter(lambda x: x[1] in ReadNovel_TagIDList and x[0] != ReadNovel_NovelID).map(
        lambda x: x[0]).distinct().collect()
    SameTagNovelList = Novel.select(Novel["NovelID"], Novel["Title"], Novel["MonthlyClicks"]).rdd \
        .filter(lambda x: x[0] in SameTagNovel_NovelIDList). \
        map(lambda x: (x[1], int(x[2]))).sortBy(keyfunc=lambda x: x[1], ascending=False).map(lambda x: x[0]).take(10)
    print("具有相同标签的其他小说中热度最高的10本小说:", SameTagNovelList)

# RecommendaByReadNovel("三国的女人")
