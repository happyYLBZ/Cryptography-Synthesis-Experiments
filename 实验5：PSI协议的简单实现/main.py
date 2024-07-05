import secrets
import gmpy2
import pybloom_live
from Crypto.PublicKey import RSA

RSA_BITS = 1024  # 设置 RSA 密钥的位数为 1024
RSA_EXPONENT = 65537  # 设置 RSA 的公开指数为 65537
RT_COUNT = 0  # 初始化 RT_COUNT 变量为 0


# 生成RSA私钥
def generate_private_key(bits=RSA_BITS, e=RSA_EXPONENT):
    # 调用 RSA 的 generate 方法生成一个私钥，其中密钥的位数为 bits，公开指数为 e
    private_key = RSA.generate(bits=bits, e=e)
    # 从私钥中生成对应的公钥
    public_key = private_key.publickey()

    return private_key

# 生成随机因子
def generate_random_factors(public_key):
    # 初始化一个空列表 random_factors，用于存储随机因子
    random_factors = []
    # 打开一个名为 'randomfactors.raw' 的文件，准备写入数据
    rff = open('randomfactors.raw','w')
    # 循环 RF_COUNT 次
    for _ in range(RF_COUNT):
        # 生成一个小于公钥 n 的随机数 r
        r = secrets.randbelow(public_key.n)
        # 计算 r 在模 n 下的逆元 r_inv
        r_inv = gmpy2.invert(r, public_key.n)
        # 计算 r 的 e 次方对 n 取模的结果，即对 r 进行 RSA 加密
        r_encrypted = gmpy2.powmod(r, public_key.e, public_key.n)
         # 将 (r_inv, r_encrypted) 添加到 random_factors 列表中
        random_factors.append((r_inv, r_encrypted))
        # 将 r_inv 写入到文件中
        rff.writelines(f"{r_inv.digits()}\n")
        # 将 r_encrypted 写入到文件中
        rff.writelines(f"{r_encrypted.digits()}\n")
    rff.close()  # 关闭文件
    return random_factors  # 返回 random_factors 列表

# 对数据进行盲化处理
def blind_data(my_data_set, random_factors, n):

    # 初始化一个空列表 A
    A = []
    # 打开一个名为 'blinddata.raw' 的文件，准备写入数据
    bdf = open('blinddata.raw','w')
    # 对 my_data_set 和 random_factors 中的每一对元素 p 和 rf 进行操作
    for p, rf in zip(my_data_set, random_factors):
        # 获取 rf 的第二个元素，即加密后的随机数 r
        r_encrypted = rf[1]
        # 计算 (p * r_encrypted) 对 n 取模的结果，即对数据进行盲化处理
        blind_result = (p * r_encrypted) % n
        # 将盲化处理的结果添加到列表 A 中
        A.append(blind_result)
        # 将盲化处理的结果写入到文件中
        bdf.writelines(f"{blind_result.digits()}\n")
    # 关闭文件
    bdf.close()
    # 返回列表 A
    return A

# 设置一个布隆过滤器
def setup_bloom_filter(private_key, data_set):
    # 设置布隆过滤器的模式为 SMALL_SET_GROWTH
    mode = pybloom_live.ScalableBloomFilter.SMALL_SET_GROWTH
    # 创建一个布隆过滤器实例 bf
    bf = pybloom_live.ScalableBloomFilter(mode=mode)
    # 对 data_set 中的每一个元素 q 进行操作
    for q in data_set:
        # 计算 q 的 private_key.d 次方对 private_key.n 取模的结果，即对 q 进行 RSA 签名
        sign = gmpy2.powmod(q, private_key.d, private_key.n)
        # 将签名结果添加到布隆过滤器 bf 中
        bf.add(sign)
    # 打开一个名为 'bloomfilter.raw' 的文件，准备写入数据
    bff = open('bloomfilter.raw','wb')
    # 将布隆过滤器 bf 的内容写入到文件中
    bf.tofile(bff)
    # 关闭文件
    bff.close()
    # 返回布隆过滤器 bf
    return bf

# 对盲化处理的数据进行签名
def sign_blind_data(private_key, A):
    # 初始化一个空列表 B
    B = []
    # 打开一个名为 'signedblinddata.raw' 的文件，准备写入数据
    sbdf = open('signedblinddata.raw','w')
    # 对列表 A 中的每一个元素 a 进行操作
    for a in A:
        # 计算 a 的 private_key.d 次方对 private_key.n 取模的结果，即对 a 进行 RSA 盲签名
        sign = gmpy2.powmod(a, private_key.d, private_key.n)
        # 将盲签名的结果添加到列表 B 中
        B.append(sign)
        # 将盲签名的结果写入到文件中
        sbdf.writelines(f"{sign.digits()}\n")
    # 关闭文件
    sbdf.close()
    # 返回列表 B
    return B

# 找出原始数据集中的哪些元素在布隆过滤器中
def intersect(my_data_set, signed_blind_data, random_factors, bloom_filter, public_key):
    # 获取公钥的 n 值
    n = public_key.n
    # 初始化一个空列表 result
    result = []
    # 对 my_data_set，signed_blind_data 和 random_factors 中的每一对元素 p，b 和 rf 进行操作
    for p, b, rf in zip(my_data_set, signed_blind_data, random_factors):
        # 获取 rf 的第一个元素，即 r 的逆元 r_inv
        r_inv = rf[0]
        # 计算 (b * r_inv) 对 n 取模的结果，即对盲签名的结果进行解盲处理
        to_check = (b * r_inv) % n
        # 如果解盲处理的结果在布隆过滤器 bloom_filter 中
        if to_check in bloom_filter:
            # 将原始数据 p 添加到列表 result 中
            result.append(p)
    # 返回列表 result
    return result


# 主程序
if __name__ == '__main__':
    # 创建客户端数据集，包含从 0 到 1024 的数，步长为 249
    client_data_set = list(range(0, 1024, 249))
    # 创建服务器数据集，包含从 0 到 1024 的所有整数
    server_data_set = list(range(0, 1024))
    # 设置随机因子的数量为客户端数据集的长度
    RF_COUNT = len(client_data_set)

    # 生成 RSA 私钥
    private_key = generate_private_key()
    # 从私钥中获取对应的公钥
    public_key = private_key.public_key()

    # 生成随机因子
    random_factors = generate_random_factors(public_key)
    # 对客户端数据集进行盲化处理
    A = blind_data(client_data_set, random_factors, public_key.n)

    # 设置布隆过滤器
    bf = setup_bloom_filter(private_key, server_data_set)

    # 对盲化处理的数据进行签名
    B = sign_blind_data(private_key, A)

    # 找出客户端数据集和服务器数据集的交集
    result = intersect(client_data_set, B, random_factors, bf, public_key)

    # 打印交集结果
    print(result)
