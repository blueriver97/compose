#!/bin/bash
set -e

# ==============================================================================
# 1. 디렉토리 및 권한 초기화
# ==============================================================================
# .ssh 디렉토리가 없으면 생성 (마운트되지 않았을 경우 대비)
if [[ ! -d "/root/.ssh" ]]; then
    mkdir -p /root/.ssh
    chmod 700 /root/.ssh
fi

# ==============================================================================
# 2. SSH Host Key 생성 (서버 신원용)
# ==============================================================================
# ssh-keygen -A: 호스트 키가 하나도 없을 때만 생성하므로 안전함
if [[ ! -f /etc/ssh/ssh_host_rsa_key ]]; then
    echo "[Entrypoint] Generating SSH Host Keys..."
    ssh-keygen -A
fi

# ==============================================================================
# 3. User Key 생성 (클러스터 통신용 - id_ed25519)
# ==============================================================================
# 키 파일이 없을 때만 생성 (재시작 시 덮어쓰기 방지)
if [[ ! -f "/root/.ssh/id_ed25519" ]]; then
    echo "[Entrypoint] Generating User SSH Key (ed25519)..."
    ssh-keygen -t ed25519 -N '' -f /root/.ssh/id_ed25519
fi

# ==============================================================================
# 4. Authorized Keys 등록 (Self-Access)
# ==============================================================================
# 공개키를 authorized_keys에 등록하여 비밀번호 없이 접속 가능하게 설정
if [[ -f "/root/.ssh/id_ed25519.pub" ]]; then
    # 중복 등록 방지를 위해 grep으로 확인 후 없으면 추가
    if ! grep -q "$(cat /root/.ssh/id_ed25519.pub)" /root/.ssh/authorized_keys 2>/dev/null; then
        echo "[Entrypoint] Adding public key to authorized_keys..."
        cat /root/.ssh/id_ed25519.pub >> /root/.ssh/authorized_keys
        chmod 600 /root/.ssh/authorized_keys
    fi
fi

# ==============================================================================
# 5. SSH Config 설정 (StrictHostKeyChecking no)
# ==============================================================================
# 설정 파일이 없거나, 해당 옵션이 없을 때만 생성/추가
if [[ ! -f "/root/.ssh/config" ]]; then
    echo "[Entrypoint] Configuring SSH Client options..."
    echo -e "Host *\n  UserKnownHostsFile /dev/null\n  StrictHostKeyChecking no" > /root/.ssh/config
    chmod 600 /root/.ssh/config
fi

# ==============================================================================
# 6. SSH Daemon 실행
# ==============================================================================
# /var/run/sshd 디렉토리가 필요함 (Ubuntu/AmazonLinux 공통)
mkdir -p /var/run/sshd

# 백그라운드로 SSHD 실행
# (Docker의 메인 프로세스는 뒤에 오는 exec "$@"가 되어야 하므로)
echo "[Entrypoint] Starting SSH Daemon..."
/usr/sbin/sshd

# ==============================================================================
# 7. 메인 커맨드 실행 (CMD 전달)
# ==============================================================================
# Dockerfile의 CMD ["/bin/bash"] 등을 여기서 실행함
exec "$@"
