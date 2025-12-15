# 1. Base Image
FROM blueriver97/amazonlinux:2023

LABEL maintainer="Data Engineer <your-email@example.com>"
LABEL description="Python Runtime Base Image"

ENV TZ=Asia/Seoul
ARG SHORT_VERSION
ENV SHORT_VERSION=${SHORT_VERSION}

# 3. Environment Settings
# Python 출력 버퍼링 비활성화 (로그 즉시 출력)
ENV PYTHONUNBUFFERED=1
# .pyc 파일 생성 방지 (이미지 크기 절약)
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /root

# 4. Install Python & Build Dependencies
# shadow-utils, gcc 등은 C 기반 라이브러리 컴파일을 위해 필수입니다.
RUN dnf -y update && \
    dnf -y install \
        python${SHORT_VERSION} \
        python${SHORT_VERSION}-devel \
        python${SHORT_VERSION}-pip \
        python${SHORT_VERSION}-wheel \
        # Common Build Tools for Python Libs (numpy, pandas, etc.)
        gcc \
        make \
        openssl-devel \
        bzip2-devel \
        libffi-devel \
        zlib-devel && \
    dnf clean all && \
    rm -rf /var/cache/dnf

# 5. python3 명령어가 설치된 버전을 바라보도록 설정
# 기본 python3, pip 심볼릭 링크 연결 (amazonlinux는 기본 python3 패키지와 충돌할 수 있으므로 명시적 연결)
RUN ln -sf /usr/bin/python${SHORT_VERSION} /usr/local/bin/python3 && \
    ln -sf /usr/bin/python${SHORT_VERSION} /usr/local/bin/python && \
    ln -sf /usr/bin/pip${SHORT_VERSION} /usr/local/bin/pip3 && \
    ln -sf /usr/bin/pip${SHORT_VERSION} /usr/local/bin/pip

# 6. Upgrade Pip & Setuptools
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# 7. (Optional) Entrypoint Inherit
# 베이스 이미지(amazonlinux:2023)의 ENTRYPOINT(ssh keygen)를 그대로 적용
# 앱 실행이 필요하면 CMD를 오버라이드
CMD ["/bin/bash"]
