# coding:utf-8
import random
import math
import csv
import matplotlib.pyplot as plt
import numpy as np
from errortools import Evaluate,maxError,minError,meanSqErr,meanError


USING_INPUT_DATA = True# 该值是用于确定算法启动模式，为True时会读取/Dataset文件夹下的数据集，为False时使用随机数据

# B:原始数据
# Q:查询集
# T:迭代次数
# eps:隐私预算
# repetitions:乘法权重算法的重复次数
def MWEM(B, Q, T, eps, repetitions):
    # 生成真实的直方图，其逻辑是，找到数据集中有效属性的最大值和最小值
    # 然后以其差值生成一个拥有差值+1个桶的直方图，以列表形式存储
    minVal = min(B)
    length = max(B) - minVal + 1
    histogram = [0]*(length)
    for val in range(len(B)):
        histogram[B[val] - minVal] += 1
    # 初始化数据合成流程
    nAtt = 1
    A = 0
    n = 0
    n = sum(histogram)
    A = [n/len(histogram) for i in range(len(histogram))]    # 生成一个分布平均的数据分布作为初始分布
    measurements = { } #mesurements是一个dict类型，其初始化时应该以{ }初始化
    # 迭代优化循环体
    for i in range(T):
        print("ITERATION ROUND#" + str(i))
        qi = ExpM(histogram, A, Q, eps/(2 * T))
        j = 1
        print("选中了"+str(Q[qi]))
        while(qi in measurements):
            qi = ExpM(histogram, A, Q, eps/(2 * T))
            print("选定的值已被观测过，启动重选，重选第"+str(j)+"次")
            j+=1
            print("选中了"+str(Q[qi]))
        evaluate = Evaluate(Q[qi],histogram)       # 对查询值进行观测并加入已观测的列表中
        lap = Laplace((2*T)/(eps*nAtt))
        measurements[qi] = evaluate + lap
        # 乘法权重更新开始
        MultiplicativeWeights(A, Q, measurements, repetitions)
    return A, histogram



# B:原始数据
# A:合成数据
# Q:查询集
# T:迭代次数
# eps:隐私预算
# ExpM-使用指数机制来选定一个查询
# 本部分算法原理：首先测量对原始数据集和合成数据运行同一个查询时其之间的误差作为打分函数，
# 根据各查询得分的多少计算出每个查询被选中的概率，之后基于这些概率随机抽取一个查询。
def ExpM(B, A, Q, eps):
    scores = [0] * len(Q)  # 初始化一个Q长度的打分列表
    for i in range(len(scores)):
        # 计算每个查询在A和B上的差异，并除以100000以进行缩放
        scores[i] = abs(Evaluate(Q[i], A) - Evaluate(Q[i], B)) / 100000
    max_score = max(scores)
    # 基于分数计算每个查询被选中的概率，并减去最大值以稳定数值
    Pr = [np.exp(eps * (score - max_score)/2.0) for score in scores]
    Pr_sum = sum(Pr)
    Pr = [p / Pr_sum for p in Pr]  # 归一化概率
    # 基于生成的概率表抽取查询并进行返回
    index = [i for i in range(len(Q))]
    return random.choices(index, Pr, k=1)[0]


# 利用给定的sigma来生成拉普拉斯随机数noise作为噪音。
def Laplace(sigma):
    return np.random.laplace(loc=0, scale=sigma)



# A:合成数据
# Q:查询集
# measurements:已观测过的查询
# repetitions:重复次数
def MultiplicativeWeights(A, Q, measurements, repetitions):
    total = sum(A)
    for iteration in range(repetitions):
        # 在每次迭代中，随机打乱查询的顺序
        update_order = list(measurements.keys())
        random.shuffle(update_order)
        # 对每个查询进行更新
        for qi in measurements:
            error = measurements[qi] - Evaluate(Q[qi], A) 
            query = queryToBinary(Q[qi], len(A))
            # 根据误差更新每个元素的权重
            for i in range(len(A)):                 
                A[i] = A[i] * math.exp(query[i] * error/(2.0*total))
            # 规范化权重以保持总和不变      
            count = sum(A)
            for k in range(len(A)):
                A[k] *= total/count


# Histo:matplotlib.plot方法所需的格式
# B:输入的数据集
# 转换查询为生成直方图所用的Plot
# 运行逻辑：确定输入数据集B的最小值后，从最小值开始，先对输入的值进行四舍五入，然后生成样本点，其个数等于四舍五入后的值
# 四舍五入的原因是加噪后的数据集内可能包含小数
def transformForPlotting(Histo, B):
    start = min(B)
    end = max(B)
    newHisto = []
    for i in range(len(Histo)):
        val = int(round(Histo[i],0))  
        for j in range(val):
            newHisto.append(start)
        start = start + 1
    return newHisto


# qi:输入的查询
# length:数据集属性长度
# 转换查询为二进制形式，用于MW机制使用
# 运行逻辑：MW机制是对符合区间的桶进行乘法权重更新，这里使用一个binary序列来代表数据集的桶是否属于区间。
# 首先，将binary全部置0，然后将输入的查询区间内的桶对应的binary值变为1。这样的话，根据这个binary值，
# MW机制就能只更新所选查询影响到的桶了。
def queryToBinary(qi,length):
    binary = [0]*length
    for i in range(length):
        if((i>=qi[0]) and i<=qi[1]):
            binary[i] = 1
    return binary


def histoDraw(real,syn,B):
    # 启动直方图绘制
    plt.figure()
    # 定桶数量
    bins = np.linspace(min(B), max(B)+1, max(B)+2)
    # Plot化数据
    HistA = transformForPlotting(real, B)
    HistB = transformForPlotting(syn, B)    
    # 制图和保存
    plt.hist([HistA,HistB],bins)
    plt.savefig("./Results/result_histo.png")
    plt.show()
    
    # 绘制折线图
    plt.plot(real, color='#1F77B4')
    plt.plot(syn, color='#FF7F0E')
    plt.savefig("./Results/result_normal.png")
    plt.show()


def randomQueries(Q_size, maxVal, minVal):
    Q = []
    for i in range (Q_size):
        down = random.randint(0,maxVal-minVal)# 下界down介于0到最大值减去最小值之间
        upper = random.randint(down,maxVal-minVal)#上界upper介于下界和最大值减去最小值之间。

        count_regen = 0 
        while (down,upper) in Q:
              #根据数据集的最大值和最小值，生成两个随机数作为查询上下界。
             down = random.randint(0,maxVal-minVal)
             upper = random.randint(down,maxVal-minVal)
             count_regen+=1
        Q.append((down,upper))
    print("查询集随机生成完毕，生成了"+str(Q_size)+"个查询，共进行规避生成"+str(count_regen)+"次")
    return Q

#导入查询集
def import_query(file_path):
    Q = []
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            Q.append((int(row[0]), int(row[1])))
            
    return Q

def main():

    
    global B
    B = []  # 一维数据
    Q_size = 60 # 查询集个数
    T = 30 # T是迭代运行次数。
    eps = 0.1 #隐私预算。
    repetitions = 20 # MW机制的重复次数

    #读取指定路径的测试数据。
    if USING_INPUT_DATA == True:
        with open('Datasets/childMentalHealth_1M.csv', 'rt') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                    try:
                        B.append(int(row[0]))
                    except ValueError as e:
                        continue
                    except IndexError as e:
                        continue
    # 测试模式：当不指定输入数据集时，允许随机生成500个记录来进行测试
    else:
        B = [random.randint(0,50) for i in range(500)] #Dataset

    maxVal = max(B)
    minVal = min(B)
    # 随机生成Q_size个查询，并对查询集中的已有查询规避
    #Q = randomQueries(Q_size, maxVal, minVal)
    # 指定查询集
    Q = import_query('Examples/queries_1D.csv')
    #启动MWEM算法为原始数据进行加噪合成
    global syntheticData
    global RealHisto
    syntheticData, RealHisto = MWEM(B, Q, T, eps, repetitions)
    # 格式化地输出合成数据到屏幕
    formattedList = ['%.3f' % elem for elem in syntheticData]
    print()
    print("Real data histogram: " + str(RealHisto))
    print()
    print("Synthetic Data: " + str(formattedList))
    print()
    print("Q: " + str(Q))
    print()
    print("Metrics:")
    print("    - MaxError: " + str(maxError(RealHisto,syntheticData, Q)))
    print("    - MinError: " + str(minError(RealHisto,syntheticData, Q)))
    print("    - MeanSquaredError: " + str(meanSqErr(RealHisto, syntheticData, Q)))
    print("    - MeanError: " + str(meanError(RealHisto,syntheticData, Q)))
    return maxError(RealHisto,syntheticData, Q), minError(RealHisto,syntheticData, Q), meanSqErr(RealHisto, syntheticData, Q), meanError(RealHisto,syntheticData, Q)

AvgMax=0
AvgMin=0
AvgMSE=0
AvgMean=0
for i in range(100):
    max_Error, min_Error, mean_SqErr, mean_Error = main()
    AvgMax += max_Error/100
    AvgMin += min_Error/100
    AvgMSE += mean_SqErr/100
    AvgMean += mean_Error/100


histoDraw(RealHisto, syntheticData, B)
print()
print()
print("    - AvgMaxError: " + str(AvgMax))
print("    - AvgMinError: " + str(AvgMin))
print("    - AvgMeanSquaredError: " + str(AvgMSE))
print("    - AvgMeanError: " + str(AvgMean))


