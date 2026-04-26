"""
CodeReview AI - API Key认证系统
为API提供用户注册、API Key发放和验证功能
"""

import uuid
import hashlib
import hmac
import time
from typing import Optional, Dict
from datetime import datetime

# 模拟数据库 - 生产环境应替换为真实数据库
_users_db: Dict[str, Dict] = {}
_api_keys_db: Dict[str, str] = {}  # api_key -> username

API_KEY_PREFIX = "cr_"


def generate_api_key() -> str:
    """生成唯一的API Key"""
    raw = f"{uuid.uuid4().hex}{time.time()}{uuid.uuid4().hex}"
    key = hashlib.sha256(raw.encode()).hexdigest()[:40]
    return f"{API_KEY_PREFIX}{key}"


def hash_password(password: str) -> str:
    """密码哈希"""
    salt = uuid.uuid4().hex
    return f"{salt}${hashlib.sha256(f'{salt}{password}'.encode()).hexdigest()}"


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    try:
        salt, pw_hash = hashed.split("$")
        return pw_hash == hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    except (ValueError, IndexError):
        return False


def register_user(username: str, password: str, email: str) -> Optional[Dict]:
    """注册新用户"""
    if username in _users_db:
        return None

    api_key = generate_api_key()
    user = {
        "username": username,
        "password_hash": hash_password(password),
        "email": email,
        "api_key": api_key,
        "created_at": datetime.now().isoformat(),
        "active": True,
        "usage_count": 0,
        "plan": "free"
    }
    _users_db[username] = user
    _api_keys_db[api_key] = username
    return {
        "username": username,
        "email": email,
        "api_key": api_key,
        "plan": "free"
    }


def authenticate(username: str, password: str) -> Optional[Dict]:
    """用户名密码登录"""
    user = _users_db.get(username)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    if not user.get("active", True):
        return None
    return {
        "username": user["username"],
        "email": user["email"],
        "api_key": user["api_key"],
        "plan": user["plan"]
    }


def validate_api_key(api_key: str) -> Optional[Dict]:
    """验证API Key"""
    if api_key not in _api_keys_db:
        return None
    username = _api_keys_db[api_key]
    user = _users_db.get(username)
    if not user or not user.get("active", True):
        return None
    # 更新使用计数
    user["usage_count"] = user.get("usage_count", 0) + 1
    return {
        "username": username,
        "plan": user["plan"],
        "usage_count": user["usage_count"]
    }


def get_user_info(username: str) -> Optional[Dict]:
    """获取用户信息"""
    user = _users_db.get(username)
    if not user:
        return None
    return {
        "username": user["username"],
        "email": user["email"],
        "api_key": user["api_key"],
        "plan": user["plan"],
        "created_at": user["created_at"],
        "usage_count": user["usage_count"]
    }


def regenerate_api_key(username: str, password: str) -> Optional[str]:
    """重新生成API Key"""
    user = _users_db.get(username)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    # 删除旧Key
    old_key = user["api_key"]
    if old_key in _api_keys_db:
        del _api_keys_db[old_key]
    # 生成新Key
    new_key = generate_api_key()
    user["api_key"] = new_key
    _api_keys_db[new_key] = username
    return new_key


# 从认证头中提取API Key的辅助函数
def extract_api_key(auth_header: Optional[str]) -> Optional[str]:
    """从Authorization头提取API Key"""
    if not auth_header:
        return None
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    if auth_header.startswith("ApiKey "):
        return auth_header[7:]
    return auth_header if auth_header.startswith(API_KEY_PREFIX) else None


# ========== 测试 ==========
if __name__ == "__main__":
    # 注册用户
    result = register_user("test_user", "test_pass", "test@example.com")
    print(f"注册结果: {result}")

    # 登录
    auth = authenticate("test_user", "test_pass")
    print(f"登录结果: {'成功' if auth else '失败'}")

    # 验证Key
    key = auth["api_key"]
    info = validate_api_key(key)
    print(f"Key验证: {info}")

    # 重新生成Key
    new_key = regenerate_api_key("test_user", "test_pass")
    print(f"新Key: {new_key}")
    old_validate = validate_api_key(key)
    print(f"旧Key验证(应失败): {old_validate}")
    new_validate = validate_api_key(new_key)
    print(f"新Key验证(应成功): {new_validate}")
