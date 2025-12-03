# base/rockylinux/Dockerfile

# 1. Base Image
FROM rockylinux:9

LABEL maintainer="Data Engineer <your-email@example.com>"
LABEL description="Rocky Linux 9 Base Image"

# 2. Environment Variables (Global)
ENV LC_ALL=C.UTF-8
ENV TZ=Asia/Seoul
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk
ENV PATH=$JAVA_HOME/bin:$PATH

# 3. Working Directory
WORKDIR /root

# 4. Configuration Setup
COPY base/rockylinux/.bashrc /root/.bashrc
COPY base/rockylinux/.vimrc /root/.vimrc

# 5. Install Packages
# htop 등 추가 패키지를 위해 epel-release 설치 필수
RUN dnf -y install epel-release && \
    dnf -y update && \
    dnf -y install --allowerasing \
        vi \
        vim \
        wget \
        curl \
        git \
        htop \
        tar \
        tree \
        findutils \
        procps-ng \
        hostname \
        lsof \
        net-tools \
        iputils \
        java-17-openjdk-devel \
        openssh-server \
        openssh-clients \
        shadow-utils \
        cronie \
        glibc-langpack-en && \
    dnf clean all && \
    rm -rf /var/cache/dnf

# 6. SSH Setup
RUN mkdir -p /var/run/sshd && \
    mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh

# 7. Entrypoint Setup
COPY ./common/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]
