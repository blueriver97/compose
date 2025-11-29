FROM blueriver97/amazonlinux:2023 AS builder

ARG PYTHON_VERSION
ENV PYTHON_VERSION=${PYTHON_VERSION}

WORKDIR /tmp

# 1. Install Build Dependencies (AL2023 uses dnf)
# 'Development Tools': gcc, make 등 필수 빌드 도구 포함
# openssl-devel, bzip2-devel, libffi-devel: 파이썬 필수 모듈 컴파일용
RUN dnf -y update && \
    dnf -y groupinstall "Development Tools" && \
    dnf -y install \
        wget \
        tar \
        gzip \
        make \
        gcc \
        openssl-devel \
        bzip2-devel \
        libffi-devel \
        zlib-devel \
        xz-devel \
        sqlite-devel \
        ncurses-devel \
        readline-devel \
        tk-devel \
        gdbm-devel \
        libuuid-devel \
        findutils && \
    dnf clean all

# 2. Download & Compile Python
# --enable-optimizations: PGO(Profile Guided Optimization) 활성화 (빌드는 느리지만 실행 속도 10~20% 향상)
# --with-lto: Link Time Optimization
RUN wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz && \
    tar xvf Python-${PYTHON_VERSION}.tgz && \
    cd Python-*/ && \
    ./configure \
        --enable-loadable-sqlite-extensions \
        --enable-optimizations \
        --with-lto \
        --prefix=/usr/local \
        --with-ensurepip=upgrade && \
    make -j "$(nproc)" && \
    make install

# 3. Upgrade pip (Builder stage에서 미리 업데이트)
RUN /usr/local/bin/python3 -m pip install --upgrade pip setuptools wheel

# ==============================================================================
# Stage 2: Runtime Image (Final)
# ==============================================================================
FROM blueriver97/amazonlinux:2023

LABEL maintainer="Data Engineer <your-email@example.com>"
LABEL description="Python Runtime Base Image"

ARG PYTHON_VERSION
ENV PYTHON_VERSION=${PYTHON_VERSION}

WORKDIR /root

# 1. Copy Compiled Artifacts from Builder
# /usr/local/bin (python3, pip3 등)
# /usr/local/lib (python 라이브러리)
# /usr/local/include (헤더 파일)
COPY --from=builder /usr/local /usr/local

# 2. Install Runtime Dependencies ONLY
# 컴파일러(gcc) 등은 제외하고, 실행에 필요한 공유 라이브러리만 설치
RUN dnf -y update && \
    dnf -y install \
        openssl-libs \
        bzip2-libs \
        libffi \
        zlib \
        xz-libs \
        sqlite-libs \
        ncurses-libs \
        readline \
        libuuid && \
    dnf clean all && \
    rm -rf /var/cache/dnf

# 3. Link Shared Libraries
# /usr/local/lib에 있는 라이브러리를 시스템이 인식하도록 갱신
RUN echo "/usr/local/lib" > /etc/ld.so.conf.d/local.conf && \
    ldconfig

# 4. Verify Installation
RUN python3 --version && pip3 --version

# 5. Base Image Settings Inherit
# 베이스 이미지(amazonlinux:2023)의 ENTRYPOINT(ssh keygen)가 그대로 적용
# 앱 실행이 필요하면 CMD를 오버라이드
CMD ["/bin/bash"]
