_LOGGING_INITIALIZED = False

def setup_console_logging(spark):
    global _LOGGING_INITIALIZED

    # 이미 설정되었다면 추가 호출 없이 반환
    if _LOGGING_INITIALIZED:
        return

    try:
        jvm = spark._jvm
        log_manager = jvm.org.apache.logging.log4j.LogManager
        core_config = jvm.org.apache.logging.log4j.core.config.Configurator
        level = jvm.org.apache.logging.log4j.Level

        # 1. 모든 루트 로그 레벨을 INFO로 변경
        # core_config.setRootLevel(level.INFO)
        # 2. 특정 패키지 강제 설정
        core_config.setLevel("org.apache.spark", level.INFO)

        _LOGGING_INITIALIZED = True
        logger = log_manager.getLogger(__name__)
        print("Log4j 2 console logging has been force-enabled at INFO level.")
    except Exception as e:
        # 에러 발생 시 로그 출력 후 중단되지 않도록 처리
        print(f"Failed to configure Log4j 2: {str(e)}")
        logger = None

    return logger
