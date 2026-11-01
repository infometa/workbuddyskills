import os

SCNET_BASE_URL = os.getenv(
    "SCNET_BASE_URL",
    "https://www.scnet.cn",
)
SCNET_TOKEN_URL = os.getenv(
    "SCNET_TOKEN_URL",
    "https://api.scnet.cn/api/user/v3/tokens",
)
SCNET_CENTER_URL = os.getenv(
    "SCNET_CENTER_URL",
    "https://www.scnet.cn/ac/openapi/v2/center",
)


USERINFO_URL = os.getenv(
    "SCNET_USERINFO_URL",
    f"{SCNET_BASE_URL.rstrip('/')}/acx/user/v1/oauth/userinfo",
)

SCNET_CLUSTER: dict[str, str] = {
    "11250": "华东一区【昆山】",
    "11274": "东北一区【哈尔滨】",
    "11276": "华东三区【乌镇】",
    "11285": "西北一区【西安】",
    "11290": "华北一区【雄衡】",
    "20057": "华东四区【山东】",
    "20058": "西南一区【四川】",
    "20073": "华东五区【山东】",
    "20078": "华中三区【武汉】",
    "20084": "华南一区【广东】",
    "20091": "华中一区【A区】"
}
