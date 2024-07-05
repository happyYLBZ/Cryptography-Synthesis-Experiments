import numpy as np

# query:指定的查询
# data:运行查询的数据
# Evaluate函数用于执行查询。其基本逻辑为：
# 对于传入的查询(x,y)，其累加传入的数据中，值在x和y区间(含x和y)的查询。
# 例如，对于一组有五个桶的数据[2,2,3,4,4]，
# 查询(2,3)会累加位于第二位和第三位的数据，即其结果为2+3=5.
def Evaluate(query,data):
    counts = 0
    for i in range(query[0],query[1]+1):
        counts += data[i]
    return counts


# real:真实数据
# synthetic:合成数据
# Q:查询集合
# maxError函数用于检测传入的两数据集间的最大差异。
# 该函数会计算传入的两数据集对于查询集Q的响应，并找出最大的差异值（以绝对值计算）
def maxError(real, synthetic, Q):
    maxVal = 0
    diff = 0
    for i in range(len(Q)):
        diff = abs(Evaluate(Q[i], real) - Evaluate(Q[i], synthetic))
        if diff > maxVal:
            maxVal = diff
    return maxVal


# real:真实数据
# synthetic:合成数据
# Q:查询集合
# meansSqError函数用于检测传入的两数据集间的均方差。
# 该函数会计算传入的两数据集对于查询集Q的响应，计算其均方差。（以绝对值计算）
def meanSqErr(real, synthetic, Q):
    errors = [(Evaluate(Q[i], synthetic) - Evaluate(Q[i], real)) for i in range(len(Q))]
    return (np.linalg.norm((errors))**2)/len(errors)


# real:真实数据
# synthetic:合成数据
# Q:查询集合
# minError函数用于检测传入的两数据集间的最小差异。
# 该函数会计算传入的两数据集对于查询集Q的响应，并找出最小的差异值（以绝对值计算）
def minError(real, synthetic, Q):
    minVal = 100000000000
    diff = 0
    for i in range(len(Q)):
        diff = abs(Evaluate(Q[i], real) - Evaluate(Q[i], synthetic))
        if diff < minVal:
            minVal = diff
    return minVal


# real:真实数据
# synthetic:合成数据
# Q:查询集合
# meanError函数用于检测传入的两数据集间的平均差异。
# 该函数会计算传入的两数据集对于查询集Q的响应，并计算差异平均值（以绝对值计算）
def meanError(real, synthetic, Q):
    errors = [abs(Evaluate(Q[i], synthetic) - Evaluate(Q[i], real)) for i in range(len(Q))]
    return sum(errors)/len(errors)