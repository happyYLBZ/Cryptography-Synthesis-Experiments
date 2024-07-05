# coding:utf-8
import random
import math
import csv
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

USING_INPUT_DATA = True# 该值是用于确定算法启动模式，为True时会读取/Dataset文件夹下的数据集，为False时使用随机数据

# B:输入数据
# rows：拆分出的行信息
# colums: 拆分出的列信息
# minRow:行最小值
# minCol:列最小值
# 这个函数就是将行、列的分桶情况组合并创造出一个二维的列表
def matrixCreation(B, rows, columns, minRow, minCol):
    # 先初始化一个全0的、规模为row*column的矩阵
    histogram = [[0]*(columns) for i in range(rows)]
    # 启动遍历，将B中数据填进矩阵中 
    for val in range(len(B[0])):
        histogram[B[0][val] - minRow][B[1][val] - minCol] += 1 
    return histogram


# B:原始数据
# Q:查询集
# T:迭代次数
# eps:隐私预算
# repetitions:乘法权重算法的重复次数
def MWEM(B, Q, T, eps, repetitions):
    # 初始化真实数据集对应的直方图
    minRow = min(B[0])
    minCol = min(B[1])
    rows = max(B[0]) - min(B[0]) + 1 #age
    columns = max(B[1]) - min(B[1]) + 1 #satisfaction

    histogram = matrixCreation(B,rows,columns,minRow,minCol)

    # 初始化数据合成流程
    nAtt = 2 # 二维
    A = []
    n = 0
    # 初始化一个分布平均的查询作为初始的分布
    # 先算所有行的每行加和，再将这些sum值再次sum，得到总矩阵的和
    # 然后平均分配给矩阵各个单元格
    m = [sum(histogram[i]) for i in range(len(histogram))]
    n = sum(m)
    value = n/(rows*columns)
    A = [[0]*(columns) for i in range(rows)]
    for i in range(len(histogram)):
        for j in range(len(histogram[i])):
            A[i][j] += value

    measurements = {} # esurements是一个dict类型，其初始化时应该以{ }初始化
    # 迭代优化循环体
    for i in range(T):
        print("ITERATION #" + str(i))
        qi =  ExpM(histogram, A, Q, eps / (2*T))
        j = 1
        print("选中了"+str(Q[qi]))
        while(qi in measurements):
            qi = ExpM(histogram, A, Q, eps/(2 * T))
            print("选定的值已被观测过，启动重选，重选第"+str(j)+"次")
            j+=1
            print("选中了"+str(Q[qi]))

        # 对查询值进行观测并加入已观测的列表中
        evaluate = Evaluate(Q[qi],histogram)
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
# 【本机制与一维时无变化！】
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




# 请根据文献、Julia代码和此处的辅助描述，来完成该函数。
# A:合成数据
# Q:查询集
# measurements:已观测过的查询
# repetitions:重复次数
def MultiplicativeWeights(A, Q, measurements, repetitions):
    m = [sum(A[i]) for i in range(len(A))]
    total = sum(m)
    for iteration in range(repetitions):
        # 在每次迭代中，随机打乱查询的顺序
        update_order = list(measurements.keys())
        random.shuffle(update_order)
        # 对每个查询进行更新
        for qi in update_order:
            error = measurements[qi] - Evaluate(Q[qi], A)
            query = queryToBinary(Q[qi], len(A[0]), len(A))
            # 根据误差更新每个元素的权重
            for i in range(len(A)):
                for j in range(len(A[i])):             
                    A[i][j] = A[i][j] * np.exp(query[i][j] * error/(2.0*total)) 
            # 规范化权重以保持总和不变      
            m = [sum(A[i]) for i in range(len(A))]
            count = sum(m)
            for k in range(len(A)):
                for l in range(len(A[k])):
                    A[k][l] *= total/count
        return A


# query:指定的查询
# data:运行查询的数据
# Evaluate函数用于执行查询。其基本逻辑为：
# 对于传入的查询{(x,y):(x,y)}，其累加传入的数据中，值在x和y区间(含x和y)的查询。
def Evaluate(query, data):
    # 查询集Q本身是一个以dict为项目的list，也就是说，每个查询都是一个dict类型数据
    # 这里，我们先将dict类型做list化来正确获取dict的左值(即在行上的查询)，绕开dict无序的限制
    # 然后我们就可以再用获取到的左值来获得dict的右值了，即可将dict还原回两个list的组合
    q_x = list(query)[0]
    q_y = query[q_x]
    counts = 0
    for i in range(q_x[0],q_x[1]+1):
        for j in range(q_y[0],q_y[1]+1):
            counts += data[i][j]
    return counts

# qi:输入的查询
# cols:行长度
# rows：列长度
# 运行逻辑：MW机制是对符合区间的桶进行乘法权重更新，这里使用一个binary序列来代表数据集的桶是否属于区间。
# MW机制就能只更新所选查询影响到的桶了。
def queryToBinary(qi, cols, rows):
    binary = [[0]*cols for i in range(rows)] 
    # 这个地方操作原理和Evaluate以及1D情况下的ToBinary类似
    q_x = list(qi)[0]
    q_y = qi[q_x]
    for i in range(rows):
        if (i >= q_x[0]) and (i <= q_x[1]):
            for j in range(cols):
                if (j >= q_y[0]) and (j <= q_y[1]):
                    binary[i][j] = 1
    return binary

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


# 随机生成Q_size个查询，并对查询集中的已有查询规避
def randomQueries(Q_size, maxVal1, minVal1,maxVal2,minVal2):
    # 此时生成的是一个列表嵌套字典的格式
    Q=[]
    count_regen = 0
    for i in range(Q_size):
        down1 = random.randint(0, maxVal1 - minVal1)
        upper1 = random.randint(down1, maxVal1 - minVal1)
        down2 = random.randint(0, maxVal2 - minVal2)
        upper2 = random.randint(down2, maxVal2 - minVal2)

        while {(down1,upper1):(down2,upper2)} in Q:
            down1 = random.randint(0, maxVal1 - minVal1)
            upper1 = random.randint(down1, maxVal1 - minVal1)
            down2 = random.randint(0, maxVal2 - minVal2)
            upper2 = random.randint(down2, maxVal2 - minVal2)
            count_regen+=1

        Q.append( {(down1,upper1):(down2,upper2)})

    print("查询集随机生成完毕，生成了"+str(Q_size)+"个查询，共进行规避生成"+str(count_regen)+"次")
    return Q

#导入查询集
def import_query(file_path):
    Q = []
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            # 我们将其转换为一个元组，并将它作为一个字典的键添加到列表Q中
            key =  (int(row[0]), int(row[1]))
            value = (int(row[2]), int(row[3]))
            Q.append({key: value})
    return Q


def histoDraw(real,syn):
    #Plot化数据和生成直方图
    print("************ REAL DATA *******************")    
    
    H = np.array(real)

    fig = plt.figure(figsize=(4, 4.2))

    ax = fig.add_subplot(111)
    ax.set_title('colorMap')
    plt.imshow(H)
    ax.set_aspect('equal')

    cax = fig.add_axes([0.12, 0.1, 0.78, 0.8])
    cax.get_xaxis().set_visible(False)
    cax.get_yaxis().set_visible(False)
    cax.patch.set_alpha(0)
    cax.set_frame_on(False)
    plt.colorbar(orientation='vertical',ax=cax)
    plt.savefig("./Results/result_2D_TRUE.png")
    plt.show()
    
    print()
    print("************ Synthetic DATA **************")
    
    H2 = np.array(syn)

    fig = plt.figure(figsize=(4, 4.2))

    ax = fig.add_subplot(111)
    ax.set_title('colorMap')
    plt.imshow(H2)
    ax.set_aspect('equal')

    cax = fig.add_axes([0.12, 0.1, 0.78, 0.8])
    cax.get_xaxis().set_visible(False)
    cax.get_yaxis().set_visible(False)
    cax.patch.set_alpha(0)
    cax.set_frame_on(False)
    plt.colorbar(orientation='vertical',ax=cax)
    plt.savefig("./Results/result_2D_SYN.png")
    plt.show()



def main():
    B = []  # 二维数据也可以是个多维的list
    Q_size = 400 # 查询集查询个数
    T = 200 # T是迭代运行次数。要注意的是，该处迭代次数不应大于上一步所生成的查询总数。
    eps = 10 # eps即epsilon，隐私预算。
    repetitions = 20 # MW机制的重复次数，一般不需更改

    B.append([])
    B.append([])
    # 使用外部数据时，该部分即为读取指定路径的测试数据。
    if USING_INPUT_DATA == True: 
        with open('Datasets/childMentalHealth_1M.csv', 'rt') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                    try:
                        B[0].append(int(row[0]))
                        B[1].append(int(row[1]))
                    except ValueError as e:
                        continue
                    except IndexError as e:
                        continue
    # 保留了一个测试模式：当不指定输入数据集时，允许随机生成一个6行2000列的记录来进行测试
    else:
        B = [[random.randint(0,100) for i in range(6)], [random.randint(0,100) for i in range(2000)]] #Dataset
    
    # 限制上下界
    maxVal1 = max(B[0])
    maxVal2 = max(B[1])
    minVal1 = min(B[0])
    minVal2 = min(B[1])

    # 随机生成Q_size个查询，并对查询集中的已有查询规避
    Q = {}
    #Q = randomQueries(Q_size, maxVal1, minVal1,maxVal2,minVal2)
    # 指定查询集
    Q = import_query("Examples/queries_2D.csv")
    global SyntheticData
    global RealHisto   
    #启动MWEM
    SyntheticData, RealHisto = MWEM(B, Q, T, eps, repetitions)

    #获得分析数据
    maxErr = maxError(RealHisto, SyntheticData, Q)
    minErr = minError(RealHisto, SyntheticData, Q)
    mse = meanSqErr(RealHisto, SyntheticData, Q)
        
    print()
    print("Real data histogram: " + str(RealHisto))
    print()
    # 格式化地输出合成数据到屏幕
    print("Synthetic Data: " + str(SyntheticData))
    print()
    print("Metrics:")
    print("  - Max Error: " + str(maxErr))
    print("  - Min Error: " + str(minErr))
    print("  - Mean Squared Error: " + str(mse))
    print("  - Mean Error: " + str(meanError(RealHisto, SyntheticData, Q)))
    print()
    return maxError(RealHisto,SyntheticData, Q), minError(RealHisto,SyntheticData, Q), meanSqErr(RealHisto, SyntheticData, Q), meanError(RealHisto,SyntheticData, Q)


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


histoDraw(RealHisto, SyntheticData)
print()
print()
print("    - AvgMaxError: " + str(AvgMax))
print("    - AvgMinError: " + str(AvgMin))
print("    - AvgMeanSquaredError: " + str(AvgMSE))
print("    - AvgMeanError: " + str(AvgMean))

