"""
- 使用 passlib 的 BCrypt 算法
- 实现 hash_password(plain_password) → 返回哈希
- 实现 verify_password(plain_password, hashed_password) → 返回 bool
"""

from passlib.context import CryptContext

# 创建密码上下文对象
# schemes: 指定使用的还算法（bcrypt 是当前最推荐的安全算法）
# deprecated:"auto"表示自动处理已弃用的方案，方便未来升级
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    对明文密码进行 Bcrypt 哈希加密

    :param plain_password: 明文密码（用户输入的原始密码）
    :return: 加密后的哈希字符串
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否与哈希密码匹配。

    :param plain_password: 明文密码（用户登录时输入的密码）
    :param hashed_password: 加密后的哈希密码
    :return: True表示匹配，False表示不匹配
    """
    return pwd_context.verify(plain_password, hashed_password)
