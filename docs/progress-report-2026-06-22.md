# API 태스크 201~214 진행 보고서

**작성일:** 2026-06-22  
**담당자:** Sucheol Jang  
**작업 범위:** 백엔드(SQLP-BE) API 문서화 및 검증  
**최종 업데이트:** 2026-06-22 (전체 완료)

---

## 완료된 작업 (14/14) ✅

| 티켓 | 브랜치 | 작업 내용 | 상태 |
|------|--------|-----------|------|
| 201 | `docs/201/login-response` | 로그인 API 응답 형식 문서화 (200/401/400) | ✅ 완료 |
| 202 | `docs/202/signup-response` | 회원가입 API 응답 형식 문서화 (201/400) | ✅ 완료 |
| 203 | `fix/203/jwt-token-issue` | JWT 토큰 발급 검증 완료, 유효기간(1h/7d) 문서화 | ✅ 완료 |
| 204 | `docs/204/auth-header` | Authorization 헤더 형식 문서화 | ✅ 완료 |
| 205 | `docs/205/analysis-validate-api` | 분석 검증 API 요청/응답 형식 문서화 | ✅ 완료 |
| 206 | `docs/206/session-post-api` | 세션 생성 POST 형식 문서화 (201/409/400) | ✅ 완료 |
| 207 | `fix/207/session-list-api` | 세션 목록 API 검증 완료, 쿼리 파라미터 상세 문서화 | ✅ 완료 |
| 208 | `docs/208/api-spec` | 프론트 연동용 통합 API 명세 (`docs/api-spec.md`) 신규 생성 | ✅ 완료 |
| 209 | `fix/209/calendar-api` | 캘린더 API 검증 완료, weeklyProblemCount/studyStreak 동작 명시 | ✅ 완료 |
| 210 | `fix/210/study-comparison-api` | 스터디원 비교 API 검증 완료, weakConcepts 산출 기준 명시 | ✅ 완료 |
| 211 | `fix/211/concept-api` | 개념 상세 API — relatedProblems에 person 필드 스펙 추가 | ✅ 완료 |
| 212 | `docs/212/understanding-choices` | 이해도 choices 확정 (이해 100/애매 50/모름 0) | ✅ 완료 |
| 213 | `docs/213/json-upload-policy` | JSON 업로드 정책 문서화 (body 전송, 파일 업로드 아님) | ✅ 완료 |
| 214 | `fix/214/growth-report-api` | 성장 리포트 API 검증 완료, period 파라미터 동작 명시 | ✅ 완료 |

---

## 주요 산출물

### 1. `api.md` 업데이트 내용 (누적)
- **로그인/회원가입**: 성공·실패 상태코드, 에러 응답 형식
- **JWT 토큰**: access(1시간)/refresh(7일) 유효기간, `/api/auth/refresh/` 엔드포인트
- **Authorization 헤더**: `Bearer <token>` 형식, 401 에러, 인증 불필요 엔드포인트 목록
- **분석 검증 API**: 인증 요구사항, 200/400 응답 형식
- **세션 생성**: 201 성공, 409 중복, 400 유효성 에러
- **세션 목록**: 필터 파라미터 상세 (search/understanding/date_from/date_to)
- **캘린더**: weeklyProblemCount = 오늘 기준 최근 7일, studyStreak = 해당 월 학습일 수
- **스터디원 비교**: session_id 필수, weakConcepts 산출 기준
- **개념 상세**: relatedProblems에 person 필드 추가
- **이해도 값**: 이해(100)/애매(50)/모름(0), average_understanding 설명
- **JSON 전송 정책**: body 기반, 파일 업로드 아님, Content-Type: application/json
- **성장 리포트**: period echo-only, 전체 기간 데이터 반환, 임계값 (개선 ≥70, 취약 <50)

### 2. `docs/api-spec.md` (신규 생성, 477줄)
프론트엔드 개발자 즉시 참고용 통합 명세:
- 전체 20개 엔드포인트 (URL/Method/인증/Request/Response/에러)
- 모든 주의사항 및 동작 상세 포함

---

## 검증된 API 동작

| API | 결과 |
|-----|------|
| JWT access+refresh 동시 발급 | 정상 ✅ |
| 세션 목록 필터링 (search/understanding/date) | 정상 ✅ |
| 세션 중복 생성 409 응답 | 정상 ✅ |
| 캘린더 DB 기반 응답 | 정상 ✅ |
| 스터디원 비교 응답 구조 | 정상 ✅ |
| 개념 상세 person 필드 포함 | 정상 ✅ (스펙 불일치 수정 완료) |
| 성장 리포트 데이터 반환 | 정상 ✅ (period 동작 명시) |

---

## 다음 단계

1. 프론트엔드 팀에 `docs/api-spec.md` 공유
2. Vue 전환 시 API 연동 작업 진행
