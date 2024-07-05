import json
import requests
import hashlib
from hashToCurve import hashToCurve, powMod, ep  # 导入自定义的哈希函数和模幂运算函数
import datetime

def send_request(tablename, H):
    # 向服务器发出请求的函数
    url = "http://localhost:5000/api/requests"  # 服务器地址
    headers = {'content-type': 'application/json'}  # 请求头部信息
    requestData = {"table_name": tablename, "H": H}  # 请求数据
    ret = requests.post(url, json=requestData, headers=headers)  # 发送 POST 请求
    if ret.status_code == 200:  # 如果请求成功
        text = json.loads(ret.text)  # 将返回的 JSON 数据解析为字典
        print(text)  # 打印返回的结果
    return text  # 返回请求结果

# 获取哈希值
def hash_username_password(username, password):
    username_password = username + password  # 将用户名和密码拼接在一起
    hash_obj = hashlib.sha224()  # 创建 SHA-224 哈希对象
    hash_obj.update(username_password.encode('utf-8'))  # 更新哈希对象的内容为拼接后的用户名和密码，并编码为 utf-8 格式
    hash_obj.digest()  # 计算哈希值
    hashed_username_password = hash_obj.hexdigest()  # 获取十六进制表示的哈希值
    return int(hashed_username_password, 16), hashed_username_password

# 盲化用户名
def blind_username(hash_value, hashed_username_password, blind_factor):
    point_x = hashToCurve(hash_value)  # 将整数哈希值映射到椭圆曲线上得到点 x
    print("生成的点x:\t", point_x)  # 打印生成的点 x
    # 取 username 的前两个字节作为表名存储盲化后的用户名 H
    bucket_name = hashed_username_password[:2]  # 取 username 的前两个字节作为表名
    bucket_name = "bucket_" + bucket_name  # 表名前加上 "bucket_"
    # 将 username 进行盲化处理
    blinded_username = powMod(point_x, blind_factor, ep.p)  # 计算 H 的 b 次方并对 ep.p 取模得到盲化后的 username
    print("table_name:\t", bucket_name)  # 打印表名
    print("blind_username:\t", blinded_username)  # 打印盲化后的用户名
    return bucket_name, blinded_username

if __name__ == '__main__':
    print("please input username:")  # 提示用户输入用户名
    user_name = input()  # 获取用户输入的用户名
    print("please input password:")  # 提示用户输入密码
    password = input()  # 获取用户输入的密码
    start = datetime.datetime.now()  # 记录开始时间
    # 盲化因子
    blind_factor = 10
    # 哈希值
    hash_value, hashed_username_password = hash_username_password(user_name, password)
    # 获取表名和盲化后的用户名
    bucket_name, blinded_username = blind_username(hash_value, hashed_username_password, blind_factor)
    # 向服务器发出请求
    result = send_request(bucket_name, blinded_username)
    end = datetime.datetime.now()  # 记录结束时间
    print("using time:\t", end - start)  # 打印程序运行时间





