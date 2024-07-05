# 导入 Flask 库，用于创建 Web 服务
from flask import Flask, jsonify, request
# 导入 re 库，用于正则表达式操作
import re
# 导入 datetime 库，用于处理日期和时间
import datetime
# 导入 CORS 库，用于处理跨源资源共享
from flask_cors import *
# 导入 pymysql 库，用于连接 MySQL 数据库
import pymysql
# 导入 json 库，用于处理 JSON 数据
import json


# 创建 Flask 应用实例
app = Flask(__name__)
# 启用 CORS，允许来自不同源的请求
CORS(app, supports_credentials=True)
# 设置 Flask 应用的调试模式为 False
app.config['DEBUG'] = False

# 定义一个函数，用于检查指定的表是否存在于数据库中
def check_table_existence(name_of_table, db_cursor):  # 这个函数用来判断表是否存在
    sql_command = "show tables;"
    db_cursor.execute(sql_command)
    list_of_tables = [db_cursor.fetchall()]
    extracted_table_list = re.findall('(\'.*?\')', str(list_of_tables))
    extracted_table_list = [re.sub("'", '', each) for each in extracted_table_list]
    if name_of_table in extracted_table_list:
        return 1  # 存在返回1
    else:
        return 0  # 不存在返回0

# 定义一个路由，该路由接受 POST 请求
@app.route('/api/requests', methods=['POST'])
def handle_requests():
    start_time = datetime.datetime.now()  # 记录开始时间
    # 建立数据库连接
    db_connect = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='ycj-18045977718q',
        database='c3server_v3',
        cursorclass=pymysql.cursors.DictCursor
    )
    # 创建游标对象
    db_cursor = db_connect.cursor()
    received_data = json.loads(request.get_data(as_text=True))  # 获取 POST 请求中的数据
    table_name = received_data['table_name']  # 获取表名
    hash_value = received_data['H']  # 获取哈希值
    print("哈希值H:\t", hash_value)

    if check_table_existence(table_name, db_cursor) == 0:  # 如果指定的表不存在
        print(table_name + ' not exists')
        end_time = datetime.datetime.now()  # 记录结束时间
        print("using time:\t", end_time - start_time)  # 打印程序运行时间
        return jsonify(result="none")  # 返回结果为 "none"
    else:
        sql_query = "SELECT * FROM " + table_name  # 构造 SQL 查询语句
        db_cursor.execute(sql_query)  # 执行 SQL 查询
        query_results = db_cursor.fetchall()  # 获取查询结果
        for row in query_results:
            second_key = list(row.keys())[1]
            if int(hash_value) == int(row[second_key]):  # 如果 Hash 值匹配
                db_connect.close()  # 关闭数据库连接
                end_time = datetime.datetime.now()  # 记录结束时间
                print("using time:\t", end_time - start_time)  # 打印程序运行时间
                return jsonify(result="match")  # 返回结果为 "match"
        end_time = datetime.datetime.now()  # 记录结束时间
        print("using time:\t", end_time - start_time)  # 打印程序运行时间
        return jsonify(result="none")  # 返回结果为 "none"

# 运行 Flask 应用
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

