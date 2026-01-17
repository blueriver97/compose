# Nginx + Let’s Encrypt (Certbot) 설정 가이드

이 프로젝트는 Docker와 Docker Compose를 사용하여 Nginx 웹 서버를 구축하고, Let's Encrypt를 통해 무료 SSL/TLS 인증서를 자동으로 발급 및 갱신하는 구성을 포함합니다.

이 구성은 별도의 개입 없이 SSL 인증서를 자동으로 갱신합니다.

Certbot 컨테이너: 12시간마다 백그라운드에서 실행되어 만료가 임박한 인증서가 있는지 확인하고 갱신(certbot renew)합니다.

Nginx 컨테이너: 6시간마다 설정을 리로드하여 갱신된 인증서를 자동으로 적용합니다.

## 준비사항

- 공인 도메인
- 포트포워딩: 공인망에서 Nginx가 실행되는 서버의 80(HTTP), 443(HTTPS) 포트로 접속 가능해야 함

---

## 환경 구성

### Nginx 설정

1. [.env](.env) 파일에서 DOMAIN 환경 변수를 작성합니다. (예: example.ddns.net)
2. \*.conf.template으로부터 환경변수 값을 치환한 후 /etc/nginx/conf.d 아래 설정을 생성합니다.
3. 값 치환은 command 영역에 작성된 명령어를 통해 수행됩니다.
4. 이후 추가할 서비스에 따라 이래 명령으로 config를 추가합니다.

```bash
  docker exec nginx bash -c "envsubst '\${DOMAIN}' < /etc/nginx/template/minio.conf.template > /etc/nginx/conf.d/minio.conf"
  docker exec nginx bash -c "envsubst '\${DOMAIN}' < /etc/nginx/template/polaris.conf.template > /etc/nginx/conf.d/polaris.conf"
  docker exec nginx nginx -s reload
```

- 실행 의존성 해결을 위한 변수 방식의 호스트 주소
  이 방식은 Docker나 클라우드 환경과 같이 인프라가 유동적인 환경에서 Nginx 컨테이너가 다른 컨테이너보다 먼저 뜨는 경우,
  정적 방식을 사용하면 연결할 서버를 찾을 수 없어 NGINX 자체가 실행되지 않습니다.
  이 경우 변수 방식을 사용하면 일단 NGINX를 띄워놓고 나중에 컨테이너가 준비되었을 때 통신할 수 있습니다.

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
