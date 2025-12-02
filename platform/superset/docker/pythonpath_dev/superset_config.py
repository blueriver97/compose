# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
# This file is included in the final Docker image and SHOULD be overridden when
# deploying the image to prod. Settings configured here are intended for use in local
# development environments. Also note that superset_config_docker.py is imported
# as a final step as a means to override "defaults" configured here
#
import logging
import os
import sys

from celery.schedules import crontab
from flask_caching.backends.filesystemcache import FileSystemCache

logger = logging.getLogger()

DATABASE_DIALECT = os.getenv("DATABASE_DIALECT")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_DB = os.getenv("DATABASE_DB")

EXAMPLES_USER = os.getenv("EXAMPLES_USER")
EXAMPLES_PASSWORD = os.getenv("EXAMPLES_PASSWORD")
EXAMPLES_HOST = os.getenv("EXAMPLES_HOST")
EXAMPLES_PORT = os.getenv("EXAMPLES_PORT")
EXAMPLES_DB = os.getenv("EXAMPLES_DB")

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = (
    f"{DATABASE_DIALECT}://"
    f"{DATABASE_USER}:{DATABASE_PASSWORD}@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_DB}"
)

# Use environment variable if set, otherwise construct from components
# This MUST take precedence over any other configuration
SQLALCHEMY_EXAMPLES_URI = os.getenv(
    "SUPERSET__SQLALCHEMY_EXAMPLES_URI",
    (
        f"{DATABASE_DIALECT}://"
        f"{EXAMPLES_USER}:{EXAMPLES_PASSWORD}@"
        f"{EXAMPLES_HOST}:{EXAMPLES_PORT}/{EXAMPLES_DB}"
    ),
)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_CELERY_DB = os.getenv("REDIS_CELERY_DB", "0")
REDIS_RESULTS_DB = os.getenv("REDIS_RESULTS_DB", "1")
RESULTS_BACKEND = FileSystemCache("/app/superset_home/sqllab")

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 60 * 60 * 24,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": REDIS_RESULTS_DB,
}
DATA_CACHE_CONFIG = CACHE_CONFIG
THUMBNAIL_CACHE_CONFIG = CACHE_CONFIG

class CeleryConfig:
    broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
        "superset.tasks.thumbnails",
        "superset.tasks.cache",
    )
    result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}"
    worker_prefetch_multiplier = 1
    task_acks_late = False
    beat_schedule = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": crontab(minute="*", hour="*"),
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            "schedule": crontab(minute=10, hour=0),
        },
    }
CELERY_CONFIG = CeleryConfig

FEATURE_FLAGS = {
    # [기본]
    "ALERT_REPORTS": True,
    "PLAYWRIGHT_REPORTS_AND_THUMBNAILS": True,  # ALERT_REPORTS 기능 사용 시, 기본 엔진인 Selenium 보다 가벼움
    "DASHBOARD_RBAC": True,  # Role 기반 접근 제어 설정
    "DASHBOARD_CROSS_FILTERS": True,  # 대시보드 내 여러 차트에 필터링 공유

    # [편의성]
    "ALLOW_ADHOC_SUBQUERY": True,  # Filter, Metrics 내 CUSTOM SQL 탭 추가
    "ENABLE_TEMPLATE_PROCESSING": True,  # SQL Lab 내 Jinja 템플릿 사용 (동적 쿼리 작성 필수)
    "TAGGING_SYSTEM": True,  # 대시보드 및 차트에 Tag(#) 설정
    "DRILL_BY": True,  # 차트 클릭 시 다른 컬럼으로 즉시 쪼개서 보기
    "ESTIMATE_QUERY_COST": True,  # 쿼리 실행 예상 비용 표시

    # [비동기 쿼리, superset_websocket 필요]
    "GLOBAL_ASYNC_QUERIES": True,  # 비동기 쿼리 지원

    # [보안 이슈 체크]
    "ALLOW_FULL_CSV_EXPORT": True,  # 전체 데이터 CSV 다운로드
    "EMBEDDED_SUPERSET": False,  # 대시보드를 외부 웹사이트에 임베딩
    "ENABLE_JAVASCRIPT_CONTROLS": False,  # 차트에 커스텀 JS 삽입 (XSS 공격에 취약)
    "ENABLE_SUPERSET_META_DB": False,  # 여러 DB 간 조인(예: MySQL + Athena 조인) 지원. (메모리 폭발)
}

# ---------------------------------------------------------
# 보안 설정
# ---------------------------------------------------------
# 1. CSRF 보호 활성화 (운영 환경 필수)
WTF_CSRF_ENABLED = True

# 2. 쿠키 보안 설정 완화 (HTTP 사용 시 필수)
# HTTPS를 적용하기 전까지는 Secure 옵션을 False로 해야 브라우저가 쿠키를 저장합니다.
# 쿠키가 없으면 무한 로그인 화면으로 이동합니다.
# HTTPS(SSL) 적용 후에는 반드시 True로 변경해야 합니다.
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True # 자바스크립트에서 쿠키 접근 차단 (보안 강화)
SESSION_COOKIE_SAMESITE = 'Lax' # 링크를 통한 접근 시에도 로그인 상태 유지(편의성 차원에서 Lax 권장)

# ---------------------------------------------------------
# GLOBAL_ASYNC_QUERIES 관련 설정
# ---------------------------------------------------------
# GLOBAL_ASYNC_QUERIES_JWT_SECRET: -> openssl rand -base64 42
# GLOBAL_ASYNC_QUERIES 활성화 시, superset-websocket/config.json 내 JWT_SECRET 값과 같아야함.

GLOBAL_ASYNC_QUERIES_JWT_SECRET = "0d9XgAqQjjl2q5SaS2N19pt7pkPr/LqZJ9NgfE6UDNWyyQMP+0yxzTSE"
GLOBAL_ASYNC_QUERIES_TRANSPORT = "ws"


# GLOBAL_ASYNC_QUERIES_WEBSOCKET_URL: 브라우저에서 superset_websocket에 연결할 수 있는 주소
# TALISMAN_CONFIG 설정에서 "connect-src"에 ws://<superset_addr>:8080 URL을 추가해야 함
# (예를 들어, Superset이 구동된 서버의 주소가 172.30.1.xx라면 "ws://172.30.1.xx:8080" 가 주소가 됨)
# Superset의 보안 정책은 기본적으로 'self'(현재 페이지가 로드된 도메인/포트)와 Mapbox만 허용하도록 엄격하게 설정되어 있으므로,
# TALISMAN_ENABLED = True 상태에서 특정 포트(8080)에 대한 접근이 허용되도록 TALISMAN_CONFIG 수정 필요

# 2025-11-27: Host IP로 접속 확인 (172.30.1.xx)
TALISMAN_ENABLED = True
TALISMAN_CONFIG = {
    "content_security_policy": {
        "base-uri": ["'self'"],
        "default-src": ["'self'"],
        "img-src": [
            "'self'",
            "blob:",
            "data:",
            "https://apachesuperset.gateway.scarf.sh",
            "https://static.scarf.sh/",
            # "https://cdn.brandfolder.io", # Uncomment when SLACK_ENABLE_AVATARS is True  # noqa: E501
            "ows.terrestris.de",
            "https://cdn.document360.io",
        ],
        "worker-src": ["'self'", "blob:"],
        "connect-src": [
            "'self'",
            "https://api.mapbox.com",
            "https://events.mapbox.com",
            "https://tile.openstreetmap.org",
            "https://tile.osm.ch",
            "https://a.basemaps.cartocdn.com",
            "ws://localhost:8080", # GLOBAL_ASYNC_QUERIES 활성화 시, 웹 브라우저가 superset_websocket에 직접 연결 가능해야 함.
            "http://localhost:8088",
        ],
        "object-src": "'none'",
        "style-src": [
            "'self'",
            "'unsafe-inline'",
        ],
        "script-src": ["'self'", "'strict-dynamic'"],
    },
    "content_security_policy_nonce_in": ["script-src"],
    "force_https": False,
    "session_cookie_secure": False,
}

GLOBAL_ASYNC_QUERIES_WEBSOCKET_URL = "ws://localhost:8080/"
GLOBAL_ASYNC_QUERIES_CACHE_BACKEND = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_HOST": "redis",
    "CACHE_REDIS_PORT": 6379,
    "CACHE_REDIS_DB": 0,
    "CACHE_DEFAULT_TIMEOUT": 60 * 60 * 24,
}

ALERT_REPORTS_NOTIFICATION_DRY_RUN = True
WEBDRIVER_BASEURL = "http://localhost:8088/"  # When using docker compose baseurl should be http://superset_app:8088/  # noqa: E501
# The base URL for the email report hyperlinks.
WEBDRIVER_BASEURL_USER_FRIENDLY = (
    #f"http://localhost:8888/{os.environ.get('SUPERSET_APP_ROOT', '/')}/"
    "http://localhost:8088/"
)
SQLLAB_CTAS_NO_LIMIT = True

ENABLE_CORS = True
CORS_OPTIONS = {
    "origins": ["*"]
}
# Rate Limit(속도 제한) 정보를 메모리 대신 Redis에 저장
RATELIMIT_STORAGE_URI = "redis://redis:6379/0"

# boto3 및 botocore의 DEBUG 로그 비활성화
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.INFO)
log_level_text = os.getenv("SUPERSET_LOG_LEVEL", "INFO")
LOG_LEVEL = getattr(logging, log_level_text.upper(), logging.INFO)

if os.getenv("CYPRESS_CONFIG") == "true":
    # When running the service as a cypress backend, we need to import the config
    # located @ tests/integration_tests/superset_test_config.py
    base_dir = os.path.dirname(__file__)
    module_folder = os.path.abspath(
        os.path.join(base_dir, "../../tests/integration_tests/")
    )
    sys.path.insert(0, module_folder)
    from superset_test_config import *  # noqa

    sys.path.pop(0)

# ----------------------------------------------------
# AUTHENTICATION CONFIG
# https://flask-appbuilder.readthedocs.io/en/latest/security.html#authentication-ldap
# 관련 설정은 여기서 -->> https://flask-appbuilder.readthedocs.io/en/latest/config.html
# 인증 유형
# AUTH_OID : OpenID용
# AUTH_DB : 데이터베이스 (사용자 이름/비밀번호)용
# AUTH_LDAP : LDAP용
# AUTH_REMOTE_USER : 웹 서버에서 REMOTE_USER 사용용
# ----------------------------------------------------
"""
from flask_appbuilder.security.manager import AUTH_LDAP
from custom_security_manager import CustomSecurityManager

AUTH_TYPE = AUTH_LDAP

# 전체 관리자 역할 이름 설정
AUTH_ROLE_ADMIN = 'Admin'

# 공용 역할 이름 설정, 인증이 필요 없음
AUTH_ROLE_PUBLIC = 'Public'

# 사용자가 스스로 등록할 수 있도록 허용
AUTH_USER_REGISTRATION = True

# 기본 사용자 등록 역할
AUTH_USER_REGISTRATION_ROLE = "Public"

# LDAP 인증을 사용할 때 LDAP 서버 설정
# AUTH_LDAP_SERVER = "ldap://ldap.example.com:389"
AUTH_LDAP_SERVER = "ldaps://ldap.example.com:636"
AUTH_LDAP_BIND_USER = "CN=AdminUser,CN=Users,DC=example,DC=com"

# LDAP 조회 시 사용하는 AdminUser 계정 패스워드
AUTH_LDAP_BIND_PASSWORD = ""

# LDAP TLS 인증
AUTH_LDAP_USE_TLS = False
AUTH_LDAP_ALLOW_SELF_SIGNED = True

# 로그인할 때마다 역할을 동기화
AUTH_ROLES_SYNC_AT_LOGIN = False

# 사용자 검색 도메인
AUTH_LDAP_SEARCH = "DC=example,DC=com"  # the LDAP search base

# 로그인 시 사용할 LDAP 정보
AUTH_LDAP_UID_FIELD = "sAMAccountName"

# Local 계정도 활성화
CUSTOM_SECURITY_MANAGER = CustomSecurityManager
"""
# Optionally import superset_config_docker.py (which will have been included on
# the PYTHONPATH) in order to allow for local settings to be overridden

try:
    import superset_config_docker
    from superset_config_docker import *  # noqa

    logger.info(
        f"Loaded your Docker configuration at " f"[{superset_config_docker.__file__}]"
    )
except ImportError:
    logger.info("Using default Docker config...")
