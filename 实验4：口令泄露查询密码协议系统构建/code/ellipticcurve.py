def inverse_mod(a, m):
    """求 a mod m 的逆元。"""

    # 如果 a 小于 0 或者大于等于 m，那么对 a 进行模 m 操作
    if a < 0 or m <= a:
        a = a % m

    # 使用扩展欧几里得算法求逆元
    c, d = a, m
    uc, vc, ud, vd = 1, 0, 0, 1
    while c != 0:
        q, c, d = divmod(d, c) + (c,)
        uc, vc, ud, vd = ud - q * uc, vd - q * vc, uc, vc

    # 此时，d 是最大公约数，且 ud*a+vd*m = d。
    # 如果 d == 1，这意味着 ud 是逆元。

    assert d == 1
    if ud > 0:
        return ud
    else:
        return ud + m


def modular_sqrt(a, p):
    """求解模 p 下 a 的平方根。"""

    # 简单的情况
    #
    if legendre_symbol(a, p) != 1:  # 如果 a 不是模 p 下的二次剩余，返回 0
        return 0
    elif a == 0:  # 如果 a 是 0，返回 0
        return 0
    elif p == 2:  # 如果 p 是 2，返回 p
        return p
    elif p % 4 == 3:  # 如果 p 模 4 等于 3，直接计算平方根
        return pow(a, (p + 1) // 4, p)

    # 将 p-1 分解为 s * 2^e，s 为奇数
    s = p - 1
    e = 0
    while s % 2 == 0:
        s /= 2
        e += 1

    # 找到一个 'n'，使得勒让德符号 n|p = -1。
    n = 2
    while legendre_symbol(n, p) != -1:
        n += 1

    # 使用 Tonelli-Shanks 算法求解平方根
    x = pow(a, (s + 1) // 2, p)
    b = pow(a, s, p)
    g = pow(n, s, p)
    r = e

    while True:
        t = b
        m = 0
        for m in range(r):
            if t == 1:
                break
            t = pow(t, 2, p)

        if m == 0:
            return x

        gs = pow(g, 2 ** (r - m - 1), p)
        g = (gs * gs) % p
        x = (x * gs) % p
        b = (b * g) % p
        r = m


def legendre_symbol(a, p):
    # 计算勒让德符号，它是数论中的一个重要概念，用于判断一个数在模 p 下是否是二次剩余
    ls = pow(a, (p - 1) // 2, p)
    return -1 if ls == p - 1 else ls


def jacobi_symbol(n, k):
    # 计算雅可比符号，它是勒让德符号的推广，用于判断一个数在模 k 下是否是二次剩余
    assert k > 0 and k & 1, "jacobi symbol is only defined for positive odd k"
    n %= k
    t = 0
    while n != 0:
        while n & 1 == 0:
            n >>= 1
            r = k & 7
            t ^= (r == 3 or r == 5)
        n, k = k, n
        t ^= (n & k & 3 == 3)
        n = n % k
    if k == 1:
        return -1 if t else 1
    return 0


class CurveFp(object):
    # 定义一个表示有限域上的椭圆曲线的类
    def __init__(self, p, a, b):
        # 初始化方法，设置椭圆曲线的参数
        self.__p = p
        self.__a = a
        self.__b = b

    def p(self):
        # 返回椭圆曲线的模数
        return self.__p

    def a(self):
        # 返回椭圆曲线的参数 a
        return self.__a

    def b(self):
        # 返回椭圆曲线的参数 b
        return self.__b

    def contains_point(self, x, y):
        # 检查一个点是否在椭圆曲线上
        return (y * y - (x * x * x + self.__a * x + self.__b)) % self.__p == 0


class Point(object):
    # 定义一个表示椭圆曲线上的点的类
    def __init__(self, curve, x, y, order=None):
        # 初始化方法，设置点的坐标和所在的椭圆曲线
        self.__curve = curve
        self.__x = x
        self.__y = y
        self.__order = order
        if self.__curve:
            assert self.__curve.contains_point(x, y)
        if order:
            assert self * order == INFINITY

    def __eq__(self, other):
        # 判断两个点是否相等
        if self.__curve == other.__curve \
                and self.__x == other.__x \
                and self.__y == other.__y:
            return 1
        else:
            return 0

    def __add__(self, other):
        # 定义点的加法运算
        if other == INFINITY:
            return self
        if self == INFINITY:
            return other
        assert self.__curve == other.__curve
        if self.__x == other.__x:
            if (self.__y + other.__y) % self.__curve.p() == 0:
                return INFINITY
            else:
                return self.double()

        p = self.__curve.p()

        l = ((other.__y - self.__y) * inverse_mod(other.__x - self.__x, p)) % p

        x3 = (l * l - self.__x - other.__x) % p
        y3 = (l * (self.__x - x3) - self.__y) % p

        return Point(self.__curve, x3, y3)

    def __sub__(self, other):
        # 定义点的减法运算
        if other == INFINITY:
            return self
        if self == INFINITY:
            return other
        assert self.__curve == other.__curve

        p = self.__curve.p()

        opi = -other.__y % p

        if self.__x == other.__x:
            if (self.__y + opi) % self.__curve.p() == 0:
                return INFINITY
            else:
                return self.double

        l = ((opi - self.__y) * inverse_mod(other.__x - self.__x, p)) % p

        x3 = (l * l - self.__x - other.__x) % p
        y3 = (l * (self.__x - x3) - self.__y) % p

        return Point(self.__curve, x3, y3)

    def __mul__(self, e):
        # 定义点的乘法运算
        if self.__order:
            e %= self.__order
        if e == 0 or self == INFINITY:
            return INFINITY
        result, q = INFINITY, self
        while e:
            if e & 1:
                result += q
            e, q = e >> 1, q.double()
        return result

    def __rmul__(self, other):
        # 定义点的右乘运算
        return self * other

    def __str__(self):
        # 定义点的字符串表示形式
        if self == INFINITY:
            return "infinity"
        return "(%d, %d)" % (self.__x, self.__y)

    def inverse(self):
        # 返回点的逆元
        return Point(self.__curve, self.__x, -self.__y % self.__curve.p())

    def double(self):
        # 返回点的二倍点
        if self == INFINITY:
            return INFINITY

        p = self.__curve.p()
        a = self.__curve.a()

        l = ((3 * self.__x * self.__x + a) * inverse_mod(2 * self.__y, p)) % p

        x3 = (l * l - 2 * self.__x) % p
        y3 = (l * (self.__x - x3) - self.__y) % p

        return Point(self.__curve, x3, y3)

    def x(self):
        # 返回点的 x 坐标
        return self.__x

    def y(self):
        # 返回点的 y 坐标
        return self.__y

    def pair(self):
        # 返回点的坐标对
        return (self.__x, self.__y)

    def curve(self):
        # 返回点所在的椭圆曲线
        return self.__curve

    def order(self):
        # 返回点的阶
        return self.__order


# 定义无穷远点
INFINITY = Point(None, None, None)

# 主函数
def __main__():

    # 定义一个失败测试的异常类
    class FailedTest(Exception):
        pass

    # 定义一个测试加法的函数
    def test_add(c, x1, y1, x2, y2, x3, y3):
        # 创建两个点
        p1 = Point(c, x1, y1)
        p2 = Point(c, x2, y2)
        # 计算这两个点的和
        p3 = p1 + p2
        print("%s + %s = %s" % (p1, p2, p3))
        # 检查结果是否正确
        if p3.x() != x3 or p3.y() != y3:
            raise FailedTest("Failure: should give (%d,%d)." % (x3, y3))
        else:
            print(" Good.")

    # 定义一个测试倍点的函数
    def test_double(c, x1, y1, x3, y3):
        # 创建一个点
        p1 = Point(c, x1, y1)
        # 计算这个点的二倍点
        p3 = p1.double()
        print("%s doubled = %s" % (p1, p3))
        # 检查结果是否正确
        if p3.x() != x3 or p3.y() != y3:
            raise FailedTest("Failure: should give (%d,%d)." % (x3, y3))
        else:
            print(" Good.")

    # 定义一个测试无穷远点倍点的函数
    def test_double_infinity(c):
        # 创建一个无穷远点
        p1 = INFINITY
        # 计算无穷远点的二倍点
        p3 = p1.double()
        print("%s doubled = %s" % (p1, p3))
        # 检查结果是否正确
        if p3.x() != INFINITY.x() or p3.y() != INFINITY.y():
            raise FailedTest("Failure: should give (%d,%d)." % (INFINITY.x(), INFINITY.y()))
        else:
            print(" Good.")

    # 定义一个测试乘法的函数
    def test_multiply(c, x1, y1, m, x3, y3):
        # 创建一个点
        p1 = Point(c, x1, y1)
        # 计算这个点的 m 倍点
        p3 = p1 * m
        print("%s * %d = %s" % (p1, m, p3))
        # 检查结果是否正确
        if p3.x() != x3 or p3.y() != y3:
            raise FailedTest("Failure: should give (%d,%d)." % (x3, y3))
        else:
            print(" Good.")

    # 创建一个椭圆曲线
    c = CurveFp(23, 1, 1)
    # 进行加法测试
    test_add(c, 3, 10, 9, 7, 17, 20)
    # 进行倍点测试
    test_double(c, 3, 10, 7, 12)
    # 进行加法测试（应该调用倍点函数）
    test_add(c, 3, 10, 3, 10, 7, 12)
    # 进行乘法测试
    test_multiply(c, 3, 10, 2, 7, 12)

    # 进行无穷远点倍点测试
    test_double_infinity(c)

    # 创建一个点
    g = Point(c, 13, 7, 7)

    # 检查点的乘法运算
    check = INFINITY
    for i in range(7 + 1):
        p = (i % 7) * g
        print("%s * %d = %s, expected %s . . ." % (g, i, p, check))
        if p == check:
            print(" Good.")
        else:
            raise FailedTest("Bad.")
        check = check + g

    # 定义一些常数
    p = 6277101735386680763835789423207666416083908700390324961279
    r = 6277101735386680763835789423176059013767194773182842284081

    c = 0x3099d2bbbfcb2538542dcd5fb078b6ef5f3d6fe2c745de65
    b = 0x64210519e59c80e70fa7e9ab72243049feb8deecc146b9b1
    Gx = 0x188da80eb03090f67cbf20eb43a18800f4ff0afd82ff1012
    Gy = 0x07192b95ffc8da78631011ed6b24cdd573f977a11e794811

    # 创建一个椭圆曲线和一个点
    c192 = CurveFp(p, -3, b)
    p192 = Point(c192, Gx, Gy, r)

    # 进行乘法测试
    d = 651056770906015076056810763456358567190100156695615665659
    Q = d * p192
    if Q.x() != 0x62B12D60690CDCF330BABAB6E69763B471F994DD702D16A5:
        raise FailedTest("p192 * d came out wrong.")
    else:
        print("p192 * d came out right.")

    # 进行乘法测试
    k = 6140507067065001063065065565667405560006161556565665656654
    R = k * p192
    if R.x() != 0x885052380FF147B734C330C43D39B2C4A89F29B0F749FEAD \
       or R.y() != 0x9CF9FA1CBEFEFB917747A3BB29C072B9289C2547884FD835:
        raise FailedTest("k * p192 came out wrong.")
    else:
        print("k * p192 came out right.")

    # 进行乘法测试
    u1 = 2563697409189434185194736134579731015366492496392189760599
    u2 = 6266643813348617967186477710235785849136406323338782220568
    temp = u1 * p192 + u2 * Q
    if temp.x() != 0x885052380FF147B734C330C43D39B2C4A89F29B0F749FEAD \
       or temp.y() != 0x9CF9FA1CBEFEFB917747A3BB29C072B9289C2547884FD835:
        raise FailedTest("u1 * p192 + u2 * Q came out wrong.")
    else:
        print("u1 * p192 + u2 * Q came out right.")

# 执行主函数
if __name__ == "__main__":
    __main__()
