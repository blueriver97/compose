# base/ubuntu/Dockerfile

# 1. Base Image
FROM ubuntu:24.04

LABEL maintainer="Data Engineer <your-email@example.com>"
LABEL description="Ubuntu 24.04 Base Image"

# 2. Environment Variables
ENV LC_ALL=C.UTF-8
ENV TZ=Asia/Seoul
ENV DEBIAN_FRONTEND=noninteractive
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# 3. Working Directory
WORKDIR /root

# 4. Configuration Setup
COPY base/ubuntu/.bashrc /root/.bashrc
COPY base/ubuntu/.vimrc /root/.vimrc

# 5. Install Packages
# mirror.kakao.com 설정은 속도 향상을 위해 주석 해제하여 사용하는 것을 권장합니다.
RUN cp /etc/apt/sources.list /etc/apt/sources.list.bak && \
    sed -i 's/archive.ubuntu.com/mirror.kakao.com/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirror.kakao.com/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        apt-utils \
        tzdata \
        net-tools \
        iputils-ping \
        lsof \
        git \
        tree \
        cron \
        vim \
        htop \
        openssh-server \
        python3-dev \
        python3-pip \
        python3-venv \
        openjdk-17-jdk && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 6. SSH Setup
RUN mkdir -p /var/run/sshd && \
    mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh

# 7. Entrypoint Setup
COPY common/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]
