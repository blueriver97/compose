# GitLab

## 트러블슈팅 (Troubleshooting)

---

### Could not create the default administrator account

- GitLab이 처음 뜰 때 DB에 root 계정을 생성(Seed)하려고 시도했지만, 초기 비밀번호가 너무 간단해 계정 생성 스크립트가 실패하여 발생함.
- .env 파일에 작성한 GITLAB_ROOT_PASSWORD 값을 복잡하게 설정하고, 볼륨 삭제 후 재시작 진행.
- 사전적 단어, 연속된 숫자, 혹은 너무 짧은 문자열은 사용할 수 없음.

```plaintext
gitlab         | Could not create the default administrator account:
gitlab         |
gitlab         | --> Password must not contain commonly used combinations of words and letters
```

1
