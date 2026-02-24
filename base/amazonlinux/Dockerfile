# platforms/amazonlinux/Dockerfile

# 1. Base Image
FROM amazonlinux:2023

LABEL maintainer="Data Engineer <your-email@example.com>"
LABEL description="Amazon Linux 2023 Base Image"

# 2. Environment Variables (Global)
ENV LC_ALL=C.UTF-8
ENV TZ=Asia/Seoul
ENV JAVA_HOME=/usr/lib/jvm/java-17-amazon-corretto
ENV PATH=$JAVA_HOME/bin:$PATH

# 3. Working Directory
WORKDIR /root

# 4. Configuration Setup
COPY ./base/amazonlinux/.bashrc /root/.bashrc
COPY ./base/amazonlinux/.vimrc /root/.vimrc

# 5. Install Packages
RUN dnf -y update && \
    dnf -y install --allowerasing \
        vi \
        vim \
        wget \
        curl \
        git \
        htop \
        tar \
        tree \
        telnet \
        findutils \
        procps-ng \
        hostname \
        lsof \
        net-tools \
        iputils \
        java-17-amazon-corretto-devel \
        aws-cli \
        openssh-server \
        shadow-utils \
        cronie && \
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
