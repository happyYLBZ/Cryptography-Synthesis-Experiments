# 设置Python源文件的编码格式为utf-8
#coding=utf-8

# 导入相关包
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair
import hashlib

# 创建名为Hash1pre的变量，并将其设置为hashlib模块中的md5函数
Hash1pre = hashlib.md5

# 进行哈希
def Hash1(w):
    # 将参数w转换为字符串，然后使用utf8编码，接着使用之前定义的MD5哈希函数进行哈希，最后将哈希值转换为16进制字符串
    hv = Hash1pre(str(w).encode('utf8')).hexdigest()
    # 打印出哈希值。
    print("hv: ", hv)
    # 使用group的hash方法对哈希值进行再次哈希，哈希的类型为G1
    hv = group.hash(hv, type=G1)
    # 返回最终的哈希值。
    return hv

#创建名为Hash2的变量，并将其设置为hashlib模块中的sha256函数
Hash2 = hashlib.sha256

# 生成公钥和私钥
def Setup(param_id='SS512'):
    # 使用PairingGroup类创建了一个名为group的配对群，配对群的参数由param_id指定。
    group = PairingGroup(param_id)
    # 在G1类型的群中随机生成了一个元素g。
    g = group.random(G1)
    # 在ZR类型的群中随机生成了一个元素alpha。
    alpha = group.random(ZR)
# 将alpha序列化后赋值给sk
sk = group.serialize(alpha)
    # 将g和g的alpha次方序列化后赋值给pk
    pk = [group.serialize(g), group.serialize(g ** alpha)]
    # 返回私钥和公钥。
return [sk, pk]



# 加密
def Enc(pk, w, param_id='SS512'):
    # 使用PairingGroup类创建了一个名为group的配对群，配对群的参数由param_id指定。
    group = PairingGroup(param_id)
    # 从公钥pk中反序列化出两个元素g和h。
    g, h = group.deserialize(pk[0]), group.deserialize(pk[1])
    # 在ZR类型的群中随机生成了一个元素r。
    r = group.random(ZR)
    # 计算配对函数pair的值，输入是消息w的哈希值和h的r次方。
    t = pair(Hash1(w), h ** r)
    # 计算g的r次方。
    c1 = g ** r
    # 将t赋值给c2。
    c2 = t
    # 打印出c2的序列化值。
    print("group.serialize(c2): ", group.serialize(c2))
    # 返回c1的序列化值和c2的序列化值的SHA256哈希值。
    return [group.serialize(c1), Hash2(group.serialize(c2)).hexdigest()]



# 计算陷门
def TdGen(sk, w, param_id='SS512'):
    # 使用PairingGroup类创建了一个名为group的配对群，配对群的参数由param_id指定。
    group = PairingGroup(param_id)
    # 从私钥sk中反序列化出一个元素。
    sk = group.deserialize(sk)
    # 计算消息w的哈希值的sk次方。
    td = Hash1(w) ** sk
    # 返回td的序列化值。
    return group.serialize(td)



# 测试
def Test(td, c, param_id='SS512'):
    # 使用PairingGroup类创建了一个名为group的配对群，配对群的参数由param_id指定。
    group = PairingGroup(param_id)
    # 从密文c中反序列化出一个元素c1。
    c1 = group.deserialize(c[0])
    # 从密文c中取出哈希值c2。
    c2 = c[1]
    # 打印出哈希值c2。
    print("c2: ", c2)
    # 从td中反序列化出一个元素。
    td = group.deserialize(td)
    # 计算陷门td和元素c1的配对值的序列化值的SHA256哈希值，然后与哈希值c2进行比较，如果相等则返回True，否则返回False。
    return Hash2(group.serialize(pair(td, c1))).hexdigest() == c2



# 主函数
if __name__ == '__main__':
    # 设置配对群的参数为'SS512'，然后调用Setup函数生成私钥和公钥。
    param_id = 'SS512'
    [sk, pk] = Setup(param_id)

    # 创建一个名为group的配对群，配对群的参数由param_id指定。
    group = PairingGroup(param_id)

    # 对关键字"yes"进行加密来生成密文。
c = Enc(pk, "yes")
# 生成陷门
    td = TdGen(sk, "yes")
    # 测试陷门和密文是否匹配，如果匹配则返回True，否则返回False。这里应该返回True。
    assert (Test(td, c))

    # 生成一个新的陷门，对应的关键字是"no"。
    td = TdGen(sk, "no")
    # 测试新的陷门和原来的密文是否匹配，这里应该返回False。
    assert (not Test(td, c))

    # 对新的关键字"Su*re"进行加密，然后测试新的陷门和新的密文是否匹配，这里应该返回False。
    c = Enc(pk, "Su*re")
    assert (not Test(td, c))

    # 对关键字"no"进行加密，然后测试新的陷门和新的密文是否匹配，这里应该返回True。
    c = Enc(pk, "no")
    assert (Test(td, c))

    # 对关键字9 ** 100进行加密，然后生成对应的陷门。
    c = Enc(pk, 9 ** 100)
    td = TdGen(sk, 9 ** 100)
    # 测试陷门和密文是否匹配，这里应该返回True。
    assert (Test(td, c))

    # 生成一个新的陷门，对应的关键字是9 ** 100 + 1。
    td = TdGen(sk, 9 ** 100 + 1)
    # 测试新的陷门和原来的密文是否匹配，这里应该返回False。
    assert (not Test(td, c))
