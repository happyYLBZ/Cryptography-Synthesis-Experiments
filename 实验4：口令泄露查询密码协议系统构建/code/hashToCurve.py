# 导入所需的库
from ellipticcurve import CurveFp, Point, INFINITY

# 定义一个类，用于存储椭圆曲线的参数
class ECCParameters():
    def __init__(self, p, a, b, Gx, Gy, o):
        self.p = p  # 素数p
        self.a = a  # 曲线参数a
        self.b = b  # 曲线参数b
        self.Gx = Gx  # 基点G的x坐标
        self.Gy = Gy  # 基点G的y坐标
        self.o = o  # 基点G的阶

# 初始化椭圆曲线参数
ep = ECCParameters(
    p=0xffffffffffffffffffffffffffffffff000000000000000000000001,
    a=0xfffffffffffffffffffffffffffffffefffffffffffffffffffffffe,
    b=0xb4050a850c04b3abf54132565044b0b7d7bfd8ba270b39432355ffb4,
    Gx=0xb70e0cbd6bb4bf7f321390b94a03c1d356c21122343280d6115c1d21,
    Gy=0xbd376388b5f723fb4c22dfe6cd4375a05a07476444d5819985007e34,
    o=0xffffffffffffffffffffffffffff16a2e0b8f03e13dd29455c5c2a3d)

# 创建椭圆曲线
curve_secp224r1 = CurveFp(ep.p, ep.a, ep.b)
# 创建基点G
G = Point(curve_secp224r1, ep.Gx, ep.Gy, ep.o)

# 定义模幂运算函数
def powMod(x, y, z) -> int:
    # 高效地计算 (x ^ y) % z
    number = 1
    while y:
        if y & 1:
            number = number * x % z
        y >>= 1  # y //= 2
        x = x * x % z
    return number

# 定义哈希到曲线的函数
def hashToCurve(x):
    # 将输入的x值赋给h
    h = x
    # 循环100次
    for k in range(0, 100):
        # 获取点的匹配y元素
        y_parity = 0  # 总是选择0
        # 计算a的值，这里的ep.p是椭圆曲线的一个参数
        a = (powMod(x, 3, ep.p) + 7) % ep.p
        # 计算y的值
        y = powMod(a, (ep.p + 1) // 4, ep.p)
        # 如果y的奇偶性与预期的y_parity不符，就用ep.p减去y
        if y % 2 != y_parity:
            y = ep.p - y

        # 尝试创建一个椭圆曲线上的点R
        try:
            R = Point(curve_secp224r1, x, y, ep.o)
        except Exception:
            # 如果创建失败，就将x加1然后继续下一次循环
            x = (x + 1) % ep.p
            continue

        # 如果R是无穷远点，或者R乘以ep.o不是无穷远点，就将x加1然后继续下一次循环
        if R == INFINITY or R * ep.o != INFINITY:
            x = (x + 1) % ep.p
            continue
        # 如果R满足条件，就返回R
        return R
    # 如果100次循环都没有找到满足条件的R，就返回h
    return h

