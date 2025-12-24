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

- [.env](.env) 파일에서 환경 변수를 작성합니다.
  - DOMAIN: `example.ddns.net`
  - CERT_PATH: `example.ddns.net`(Prod), `example.ddns.net-0001`(Staging)
- \*.conf.template으로부터 환경변수 값을 치환한 후 /etc/nginx/conf.d 아래 설정을 생성합니다.
- 값 치환은 command 영역에 작성된 명령어를 통해 수행됩니다.

  ```bash
      for template in /etc/nginx/template/*.template; do
        filename=$$(basename \"$$template\" .template)
        envsubst $${DOMAIN} < \"$$template\" > \"/etc/nginx/conf.d/$${filename}.conf\"
      done
  ```

  ```
    docker exec nginx envsubst $${DOMAIN} < /etc/nginx/template/minio.conf.template > /etc/nginx/conf.d/minio.conf
    docker exec nginx envsubst $${DOMAIN} < /etc/nginx/template/minio.conf.template > /etc/nginx/conf.d/minio.conf
  ```

```plantext
server {
    listen 80;
    listen [::]:80;
    server_tokens off;

    server_name ${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl; # managed by Certbot
    listen [::]:443 ssl; # managed by Certbot
    server_tokens off;

    server_name ${DOMAIN}; # managed by Certbot

    root /var/www/html;
    index index.html index.htm index.nginx-debian.html;

    ssl_certificate /etc/letsencrypt/live/${CERT_PATH}/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/${CERT_PATH}/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

    location / {
        root /usr/share/nginx/html;
        index index.html;
        # proxy_pass http://my-web-app:3000;
    }
}
```

### 모듈형 설정 관리 (Legacy)

Nginx 설정을 유연하게 확장할 수 있도록 모듈형 구조를 지원합니다. default.conf.template 파일 내부에 include /etc/nginx/include.d/\*.conf; 구문이 포함되어 있어,
별도의 메인 설정 수정 없이 새로운 서비스를 추가할 수 있습니다.

- 설정 방법
  platform/nginx-certbot/data/include/ 디렉토리에 .conf 확장자로 설정 파일을 배치합니다.
  Nginx 컨테이너 실행 시 해당 디렉토리의 모든 설정 파일이 HTTPS(443) 서버 블록 내부에 자동으로 포함됩니다.
  메인 템플릿 파일을 건드리지 않고도 서비스별로 프록시 설정을 격리하여 관리할 수 있어 유지보수성이 향상됩니다.

  ```plantext
  # 서비스 프록시 연동 예시 (MinIO)
  location /minio {
      rewrite ^/minio/(.*) /$1 break;

      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;

      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";

      proxy_pass http://minio-server:9001;
  }
  ```

  - minio.conf는 /minio 경로로 들어오는 요청을 내부 minio-server:9001로 전달하며, WebSocket 통신을 위한 Upgrade 헤더 설정을 포함하고 있습니다.
  - 프록시를 통해 접근할 경우, MinIO 서버가 올바른 리다이렉션 경로를 인지할 수 있도록 `MINIO_BROWSER_REDIRECT_URL`을 설정해야 합니다.

- 설정 적용
  ```bash
  docker exec nginx nginx -s reload
  ```

### 초기화 스크립트 실행

- 인증서를 발급하는 스크립트입니다.
- 도메인과 이메일 주소를 `init-letsencrypt.sh`에 추가합니다.
- No-IP를 사용하는 경우, `*.example.ddns.net` 방식의 Wildcard 방식은 사용할 수 없습니다.
- 명시적으로 서브도메인을 추가해야 발급된 인증서에서 여러 도메인을 같이 처리할 수 있습니다.

```bash
domains=(example.ddns.net subdomain.example.ddns.net) # 본인의 도메인
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
