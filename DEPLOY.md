# Vercel 배포 가이드 (dh_bioreport)

## ⚠️ "repository does not contain the requested branch" 오류

**원인:** GitHub 저장소가 **비어 있음** (코드를 아직 올리지 않음). Vercel은 `main` 브랜치의 커밋이 있어야 배포할 수 있습니다.

**해결:** 아래 「GitHub에 코드 올리기」를 먼저 완료한 뒤, Vercel에서 프로젝트를 **다시 Import** 하거나 **Redeploy** 하세요.

### GitHub에 코드 올리기 (GitHub Desktop)

1. [GitHub Desktop](https://desktop.github.com) 설치 후 실행
2. **File → Add local repository**
3. 폴더 선택: `bio-news-report` (이 프로젝트 폴더)
4. "not a git repository" → **create a repository** → Create
5. 왼쪽 변경 파일 확인 → Summary: `Initial commit` → **Commit to main**
6. **Publish repository** (또는 **Push origin**)
   - 저장소 이름: `dh_bioreport`
   - Private 권장
7. 브라우저에서 github.com → 해당 저장소 → **파일 목록이 보이는지** 확인 (README, package.json 등)

### Vercel 다시 연결

1. Vercel → **Add New → Project** → 방금 Push한 저장소 선택
2. **Production Branch:** `main` (기본값)
3. **Deploy**

---

## 배포 전 점검 결과

| 항목 | 상태 |
|------|------|
| `package.json` — build/dev/start 스크립트 | ✅ |
| `next.config.ts` — Next.js 15 TypeScript 설정 | ✅ (`.js` 아님, Vercel 동일 지원) |
| `vercel.json` — 프레임워크·빌드 명령 | ✅ |
| `.gitignore` — node_modules, .next, .env.local | ✅ |
| `ADMIN_PASSWORD` — Vercel 환경 변수 필요 | ⚠️ 아래 「관리자 비밀번호」 참고 |

### 관리자 비밀번호 (Vercel)

배포된 `/admin` 은 서버에 등록한 비밀번호 없이는 열리지 않습니다.

1. Vercel 대시보드 → 프로젝트 **dh_bioreport** (또는 연결한 이름)
2. **Settings** → 왼쪽 메뉴 **Environment Variables**
3. **Add New**
   - **Key:** `ADMIN_PASSWORD`
   - **Value:** 로컬 `.env.local` 과 동일하게 쓸 관리자 비밀번호
   - **Environments:** Production (필요 시 Preview 포함)
4. **Save** 후 **Deployments** 탭 → 최신 항목 **Redeploy**

로컬만 설정하고 Vercel에 넣지 않으면, 배포 URL의 `/admin` 에서 「비밀번호가 아직 설정되지 않았습니다」 안내가 나옵니다.

**Vercel 프로젝트 이름:** `dh_bioreport`

**예상 URL:** `https://dh-bioreport.vercel.app` (또는 Vercel이 부여한 도메인)

---

로컬에서 빌드 테스트:

```bash
npm install
npm run build
```

---

자세한 GitHub·Vercel·모바일 체크리스트는 프로젝트 관리자에게 전달된 배포 안내 문서를 참고하세요.
