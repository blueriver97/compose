# Vault

- [설치 및 준비](#설치-및-준비)
  - [초기화 (최초 1회)](#초기화-최초-1회)
  - [봉인 해제 (서버 기동 시)](#봉인-해제-서버-기동-시)
  - [Userpass 인증 활성화](#userpass-인증-활성화)

- [사용자 관리](#사용자-관리)
  - [사용자 생성 및 삭제](#사용자-생성-및-삭제)
  - [사용자 정보 조회](#사용자-정보-조회)

- [정책 관리](#정책-관리)
  - [정책 파일 생성](#정책-파일-생성)
  - [정책 생성 및 삭제](#정책-생성-및-삭제)
  - [정책 조회](#정책-조회)

- [사용자-정책 연동](#사용자-정책-연동)
  - [Identity 엔티티 생성](#identity-엔티티-생성)
  - [엔티티 ID 조회](#엔티티-id-조회)
  - [엔티티와 정책 연동](#엔티티와-정책-연동)
  - [엔티티와 역할 연동](#엔티티와-역할-연동)
  - [엔티티 및 역할 정책 확인](#엔티티-및-역할-정책-확인)

- [사용법](#사용법)
  - [로그인](#로그인)
  - [시크릿 저장 및 조회](#시크릿-저장-및-조회)
  - [토큰 발급](#토큰-발급)

## 설치 및 준비

---

### 초기화 (최초 1회)

```bash
vault operator init
```

### 봉인 해제 (서버 기동 시)

```bash
vault operator unseal <Unseal Key1>
vault operator unseal <Unseal Key2>
vault operator unseal <Unseal Key3>
```

### 루트 로그인

```bash
vault login <Root Token>
```

### Userpass 인증 활성화

```bash
vault auth enable userpass
```

## 정책 관리

---

### 정책 파일 생성

```kubernetes helm
# example-policy.hcl
path "secret/data/*" {
    capabilities = ["create", "read", "update", "delete"]
}

path "secret/metadata/*" {
    capabilities = ["create", "read", "update", "delete"]
}
```

### 정책 생성 및 삭제

```bash
vault policy write <policy_name> <policy_file>
# vault policy write my-policy example-policy.hcl

vault policy delete <policy_name>
# vault policy delete my-policy
```

### 정책 조회

```bash
vault policy list
```

## 사용자 관리

---

### 사용자 생성 및 삭제

```bash
vault write auth/userpass/users/<username> \
    password=<password> \
    policies=<policy_name>

# vault write auth/userpass/users/johndoe \
#    password=mysecretpassword \
#    policies=my-policy
```

```bash
vault delete auth/userpass/users/<username>
# vault delete auth/userpass/users/johndoe
```

### 사용자 정보 조회

```bash
vault read auth/userpass/users/<username>
# vault read auth/userpass/users/johndoe
```

## 사용자-정책 연동

---

### Identity 엔티티 생성

```bash
vault write identity/entity/name/<entity_name>
# vault write identity/entity/name/johndoe-entity
```

### 엔티티 ID 조회

```bash
vault read identity/entity/name/<entity_name>
# vault read identity/entity/name/johndoe-entity
```

### 엔티티와 정책 연동

```bash
vault write identity/role/<role_name> \
    policies=<policy_name> \
    bound_entity_ids=<entity_id>

# vault write identity/role/johndoe-role \
#     policies=my-policy \
#     bound_entity_ids=<entity_id>
```

### 엔티티와 역할 연동

```bash
vault write auth/userpass/users/<username>/entity \
    id=<entity_id>

# vault write auth/userpass/users/johndoe/entity \
#    id=<entity_id>
```

### 엔티티 및 역할 정책 확인

```bash
vault read identity/role/<role_name>
# vault read identity/role/johndoe-role
```

## 사용법

---

### 시크릿 저장 및 조회

```bash
vault kv put <path> <key>=<value>
# vault kv put secret/my-secret password=1234

vault kv get <path>
# vault kv get secret/my-secret
```

### 토큰 발급

```bash
vault token create -policy=<policy_name> -ttl=<expired_time>
# vault token create -policy=my-policy -ttl=24h
```
