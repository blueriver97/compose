# HTTPS 자체 인증서 발급 가이드 (mkcert 활용)

<!-- TOC -->

- [HTTPS 자체 인증서 발급 가이드 (mkcert 활용)](#https-자체-인증서-발급-가이드-mkcert-활용)
  - [개요](#개요)
  - [1. 요구사항](#1-요구사항)
  - [2. mkcert 설치](#2-mkcert-설치)
    - [macOS](#macos)
  - [3. 루트 CA 설치](#3-루트-ca-설치)
  - [4. 인증서 발급](#4-인증서-발급)
  - [5. /etc/hosts 설정](#5-etchosts-설정)
  - [6. Nginx 적용 예시](#6-nginx-적용-예시)
    - [설정 적용](#설정-적용)
  - [7. 브라우저 연결 테스트](#7-브라우저-연결-테스트)
  - [8. 원격 클라이언트 RootCA 배포](#8-원격-클라이언트-rootca-배포)
    - [8.1 RootCA 파일 복사](#81-rootca-파일-복사)
    - [8.2 클라이언트 OS별 설치 방법](#82-클라이언트-os별-설치-방법)
  - [9. 주의사항](#9-주의사항)
  - [10. 참고 링크](#10-참고-링크)

<!-- TOC -->

---

## 개요

로컬 개발 환경에서 HTTPS를 구성할 때, 브라우저에서 "주의 요망" 경고 없이 신뢰할 수 있는 인증서를 사용하려면 CA(인증기관)를 시스템의 신뢰 저장소에 등록해야 합니다.

`mkcert`는 로컬 전용 CA를 생성 및 설치하고, 해당 CA로 서명된 인증서를 발급해 주는 도구입니다.

이를 통해 개발 환경에서도 프로덕션과 유사하게 브라우저 경고 없는 HTTPS 환경을 구축할 수 있습니다.

---

### 1. 요구사항

- 로컬 또는 원격 서버에 `mkcert`를 설치하고 실행할 수 있는 권한
- Nginx 등 웹 서버 설정을 변경하고 재시작할 수 있는 권한
- `/etc/hosts` 파일 수정 권한 (또는 사내 DNS 설정 권한)

---

### 2. mkcert 설치

- macOS

```bash
brew install mkcert
```

- Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y libnss3-tools wget

# 최신 버전 다운로드 (Linux amd64 기준)
wget -O mkcert [https://github.com/FiloSottile/mkcert/releases/latest/download/mkcert-$(uname](https://github.com/FiloSottile/mkcert/releases/latest/download/mkcert-$(uname) -s)-amd64

# 실행 권한 부여 및 이동
chmod +x mkcert
sudo mv mkcert /usr/local/bin/
```

---

### 3. 루트 CA 설치

- 시스템 및 브라우저의 신뢰 저장소에 로컬 루트 CA를 등록합니다.
- 이 명령어를 실행한 기기(서버/PC)에서만 해당 CA가 신뢰됩니다.

```bash
mkcert -install

mkcert -CAROOT
```

---

### 4. 인증서 발급

개발용 도메인(예: `.example.com`)에 대한 와일드카드 인증서를 발급합니다.

```bash
cd cert
mkcert '*.example.com'
```

생성되는 파일:

- `_wildcard.example.com.pem`: 서버 인증서 (공개키 포함)
- `_wildcard.example.com-key.pem`: 개인키 (비밀키)

---

### 5. /etc/hosts 설정

로컬 DNS 해석을 위해 호스트 파일을 수정합니다.

```text
127.0.0.1 example.com
127.0.0.1 service-1.example.com
127.0.0.1 service-2.example.com
```

---

### 6. Nginx 적용 예시

- 발급받은 인증서를 Nginx 설정에 적용합니다.

```nginx
# HTTP -> HTTPS 리다이렉트
server {
    listen 80;
    server_name *.example.com;
    return 301 https://$host$request_uri;
}

# HTTPS 설정
server {
    listen 443 ssl;
    server_name *.example.com;

    # 인증서 경로 설정
    ssl_certificate     /etc/nginx/_wildcard.example.com.pem;
    ssl_certificate_key /etc/nginx/_wildcard.example.com-key.pem;

    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    location / {
        root /usr/share/nginx/html;
        index index.html;
    }
}
```

- 설정 적용

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

### 7. 브라우저 연결 테스트

1. 브라우저 주소창에 `https://service.example.com` 입력
2. 기대 동작: 주소창에 자물쇠 아이콘이 표시되며, "주의 요망" 경고가 뜨지 않아야 함.

문제가 발생한다면?

- `mkcert -install`이 정상적으로 수행되었는지 확인
- 인증서 파일 경로(`ssl_certificate`)가 정확한지 확인
- 브라우저를 완전히 종료 후 재실행

---

## 원격 클라이언트 RootCA 설치

- 서버가 아닌 다른 클라이언트(팀원 PC 등)에서 접속할 때도 신뢰하려면, 서버의 RootCA를 클라이언트에 설치해야 합니다.

### 8.1 RootCA 파일 복사

서버에서 RootCA 경로를 확인하고 클라이언트로 복사합니다.

```bash
# RootCA 경로 확인
mkcert -CAROOT

# 파일 전송 예시 (scp 또는 rsync)
rsync -avP $(mkcert -CAROOT)/rootCA.pem user@client-ip:~/rootCA.pem
```

### 8.2 클라이언트 OS별 설치 방법

macOS

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/rootCA.pem
```

- 또는 키체인에서 `mkcert` 검색 후, `이 인증서 사용 시: 항상 신뢰` 설정 적용
- 브라우저 완전 종료 후 재시도

Ubuntu / Debian

```bash
sudo cp ~/rootCA.pem /usr/local/share/ca-certificates/mkcert-rootCA.crt
sudo update-ca-certificates
```

Windows

1. `rootCA.pem` 파일 확장자를 `rootCA.crt`로 변경
2. 파일 더블 클릭 → 인증서 설치
3. 저장소 위치를 "신뢰할 수 있는 루트 인증 기관"으로 선택하여 설치

---

## 주의사항

- 보안: `mkcert`로 발급한 인증서와 RootCA는 로컬 개발 및 테스트 환경에서만 사용해야 합니다.
- 운영(Production) 환경에서는 반드시 공인 CA(Let's Encrypt 등)를 사용하세요.
- RootCA 관리: `rootCA-key.pem` 파일이 유출되면 보안 위험이 있으므로 안전하게 관리해야 합니다.
- 와일드카드 범위: `.example.com`는 `service.example.com`는 커버하지만, `test.service.example.com`와 같은 2단계 서브도메인은 커버하지 않을 수 있습니다.

---

## 참고 링크

- [mkcert GitHub Repository](https://github.com/FiloSottile/mkcert)
