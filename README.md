# Repository Base (Project Template)

이 저장소는 팀의 표준 개발 환경, 보안 설정(TruffleHog), 코드 품질 분석(SonarQube), AI 커밋 메시지 작성 도구가 통합된 기본 템플릿 저장소입니다.

새로운 프로젝트를 시작할 때 이 저장소를 템플릿으로 사용하여 생성하십시오.

---

## 1. 주요 기능 (Features)

- 보안 (Security): TruffleHog를 통한 비밀 키(Secret Key) 커밋 방지
- 품질 (Quality): SonarQube/SonarCloud 연동 자동화
- 자동화 (Automation): pre-commit 훅을 이용한 코드 포맷팅(Prettier) 및 커밋 메시지 검사
- AI 지원 (AI Assistant): OpenCommit(Gemini)을 이용한 커밋 메시지 자동 작성

---

## 2. 필수 요구 사항 (Prerequisites)

이 템플릿을 사용하기 위해 로컬 환경에 다음 도구들이 설치되어 있어야 합니다.

- Node.js (v22 이상)
  - macOS: `brew install node`
  - Ubuntu: `curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt install -y nodejs`
  - Amazon Linux 2023: `sudo dnf install nodejs22`

- Python (v3.11)
  - macOS: `brew install python@3.11`
  - Ubuntu: `sudo add-apt-repository ppa:deadsnakes/ppa -y && sudo apt install python3.11 python3.11-venv`
  - Amazon Linux 2023: `sudo dnf install python3.11 python3.11-devel`

- GitHub CLI (gh) (시크릿 자동 등록)
  - macOS: `brew install gh`
  - Ubuntu: `sudo apt install gh`
  - Amazon Linux 2023: `sudo dnf install 'dnf-command(config-manager)' & sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo & sudo dnf install gh`

---

## 3. 초기 설정 (Setup)

저장소를 Clone 받은 후, 프로젝트 루트에서 다음 명령어를 최초 한 번 실행하십시오.

```bash
npm run setup
```
