# Nginx + Let’s Encrypt (Certbot) 설정 가이드

이 프로젝트는 Docker와 Docker Compose를 사용하여 Nginx 웹 서버를 구축하고, Let's Encrypt를 통해 무료 SSL/TLS 인증서를 자동으로 발급 및 갱신하는 구성을 포함합니다.

이 구성은 별도의 개입 없이 SSL 인증서를 자동으로 갱신합니다.

Certbot 컨테이너: 12시간마다 백그라운드에서 실행되어 만료가 임박한 인증서가 있는지 확인하고 갱신(certbot renew)합니다.

Nginx 컨테이너: 6시간마다 설정을 리로드하여 갱신된 인증서를 자동으로 적용합니다.

## 준비사항

- 공인 도메인
- 포트포워딩: 외부에서 서버의 80(HTTP), 443(HTTPS) 포트로 접속 가능해야 함

---

## 환경 구성

### Nginx 설정

- `example.ddns.net` 값을 실제 도메인으로 교체합니다.

```plantext
server {
    listen 80;
    server_name example.ddns.net; # [수정 필요] 본인의 도메인 입력
    server_tokens off;

    # Let's Encrypt 인증서 발급을 위한 챌린지 경로
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # 그 외 모든 요청은 HTTPS로 리다이렉트
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name example.ddns.net; # [수정 필요] 본인의 도메인 입력
    server_tokens off;

    # SSL 인증서 경로 (init 스크립트로 생성됨)
    ssl_certificate /etc/letsencrypt/live/example.ddns.net/fullchain.pem; # [수정 필요]
    ssl_certificate_key /etc/letsencrypt/live/example.ddns.net/privkey.pem; # [수정 필요]
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        # 예시: 내부의 다른 서비스로 프록시 (필요시 수정)
        root /usr/share/nginx/html;
        index index.html;

        # proxy_pass http://my-web-app:3000;
    }
}
```

### 초기화 스크립트 실행

- 최초 실행 시 인증서가 없어 Nginx가 시작되지 않을 때, 인증서 발급하는 스크립트입니다.
- 도메인과 이메일 주소를 `init-letsencrypt.sh`에 추가합니다.

```bash
domains=(example.ddns.net) # 본인의 도메인
email="your-email@example.com" # 본인의 이메일
staging=0 # 테스트 시 1, 실제 발급 시 0
```

```bash
./init-letsencrypt.sh
```

- 스크립트가 실행되면 다음 과정이 자동으로 진행됩니다
  1. 기존 더미 인증서 삭제 (존재할 경우)

  2. 더미 인증서 다운로드 및 Nginx 실행

  3. 기존 더미 인증서 삭제 후 진짜 Let's Encrypt 인증서 요청

  4. Nginx 설정 리로드

### 서버 실행

```bash
docker-compose up -d
```

---

## 원문 참고

This repository is accompanied by
a [step-by-step guide on how to set up nginx and Let’s Encrypt with Docker](https://medium.com/@pentacent/nginx-and-lets-encrypt-with-docker-in-less-than-5-minutes-b4b8a60d3a71).
