import pymysql
import hashlib
from hashToCurve import hashToCurve, powMod, ep


# 处理数据
def process(username, password, cursor, index, b):
    # 将用户名和密码连接起来
    u = username + password
    # 使用 SHA-224 哈希函数对连接后的字符串进行哈希处理
    m = hashlib.sha224()
    m.update(u.encode('utf-8'))
    m.digest()
    u = m.hexdigest()
    # 将哈希值转换为十六进制，并将其转换为一个整数
    h = int(u, 16)
    # 将整数映射到一个特定的曲线上
    H = hashToCurve(h)
    print("H:\t", H)
    # 取u前两个字节作为表名存储盲化后的用户名H
    table_name = u[:2]
    table_name = "bucket_" + table_name
    # 对u进行盲化处理
    u = powMod(H, b, ep.p)
    print("table_name:\t", table_name)
    print("username:\t", u)
    # 创建SQL语句 (创建表)
    create_table = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            user_index VARCHAR(100) NOT NULL,
            username VARCHAR(100) NOT NULL
        );
    '''
    # 执行 SQL 语句，创建表
    cursor.execute(create_table)
    # 将整数index转换为字符串
    str_index = str(index)
    # 创建SQL插入语句
    insert_data = f"INSERT INTO {table_name} (user_index, username) VALUES ('{str_index}','{u}')"
    # 执行SQL语句，插入数据
    cursor.execute(insert_data)


if __name__ == "__main__":
    # 建立数据库连接
    connect = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='ycj-18045977718q',
        database='c3server_v3',
        cursorclass=pymysql.cursors.DictCursor
    )
    # 创建游标对象
    cursor = connect.cursor()

    # SQL语句 (创建信息表)
    create_information_table = '''
        CREATE TABLE IF NOT EXISTS information (
            username VARCHAR(100) NOT NULL,
            password VARCHAR(100) NOT NULL
    );
    '''
    # 执行 SQL 语句
    cursor.execute(create_information_table)

    # 向信息表插入10万条数据
    for i in range(100000):
         user_name=i*100
         user_password=user_name
         sql = "INSERT INTO information (username, password) VALUES (%s, %s)"
         values = (user_name, user_password)
         cursor.execute(sql, values)

    # 处理数据
    sqlQuery = "SELECT * FROM information"
    cursor.execute(sqlQuery)
    results = cursor.fetchall()
    b = 10
    index = 1
    for data in results:
        username = data['username']
        pwd = data['password']
        print("username:" + username + " pwd:" + pwd)
        process(username, pwd, cursor, index, b)
        index += 1

    # 关闭游标和数据库连接
    cursor.close()
    connect.commit()
    connect.close()
    print("End...")


