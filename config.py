from pydantic import BaseModel
from orjson import loads, dumps, OPT_INDENT_2

from typing import Literal, Optional

SSL_MODES = Literal["disable", "allow", "prefer",
                    "require", "verify-ca", "verify-full"]


class DataBaseConfig(BaseModel):
    database: str = "postgres"
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "password"
    sslmode: SSL_MODES = "allow"
    sslrootcert: Optional[str] = None
    minconn: int = 1
    maxconn: int = 10


class Config(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
    jwt_key: str = ""
    dll_path: Optional[str] = None
    db_config: DataBaseConfig = DataBaseConfig()


try:
    with open("config.json", "rb") as config_file:
        config = Config(**loads(config_file.read()))
except:
    config = Config()

with open("config.json", "wb") as config_file:
    config_file.write(dumps(config.model_dump(), option=OPT_INDENT_2))

HOST = config.host
PORT = config.port
JWT_KEY = config.jwt_key
DLL_PATH = config.dll_path
DB_NAME = config.db_config.database
DB_HOST = config.db_config.host
DB_PORT = config.db_config.port
DB_USER = config.db_config.user
DB_PASSWORD = config.db_config.password
DB_SSLMODE = config.db_config.sslmode
DB_SSLROOTCERT = config.db_config.sslrootcert
DB_MINCONN = config.db_config.minconn
DB_MAXCONN = config.db_config.maxconn