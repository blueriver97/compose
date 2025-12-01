# Vault 서버 설정

# 클러스터 주소 설정 (클러스터 환경에서 필요)
# 클러스터링을 사용하는 경우 활성화 필요
# cluster_addr = "http://127.0.0.1:8201"

# 데이터 저장소 설정 (예: 파일 시스템)
storage "file" {
  path = "/vault/data"
}

# 리스너 설정 (TLS 비활성화는 운영 환경에서는 비추천)
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
  # tls_cert_file = "/path/to/cert.pem"
  # tls_key_file  = "/path/to/key.pem"
}

# API 주소 설정
api_addr = "http://vault:8200"

# 로그 레벨 설정
log_level = "info"

# 메모리 잠금 비활성화 (컨테이너 환경 등에서 필요할 수 있음)
disable_mlock = true

# 텔레메트리 비활성화 (모니터링/알람, 로그 수집, 사용량 통계 정보)
disable_telemetry = true

# 기본 TTL 및 최대 TTL 설정
default_lease_ttl = "24h"
max_lease_ttl     = "72h"

# 웹 UI 활성화 설정
ui = true

# Userpass 인증 활성화
auth "userpass" {
  path = "userpass"
}
