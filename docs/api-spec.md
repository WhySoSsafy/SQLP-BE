# SQLP API 명세 (프론트 연동용)

Base URL: /api

## 공통

### 인증 헤더
```
Authorization: Bearer <access_token>
```

### 공통 에러 형식
```json
{ "ok": false, "code": "...", "message": "...", "errors": [...] }
```

### understanding 값
`이해` / `애매` / `모름`

---

## 인증

### POST /api/auth/login/
인증 불필요

**Request**
```json
{ "email": "...", "password": "..." }
```

**Response 200**
```json
{ "access": "...", "refresh": "...", "user": { "id": "...", "name": "...", "email": "..." } }
```

**Error 401** — invalid credentials  
**Error 400** — missing fields

---

### POST /api/auth/register/
인증 불필요

**Request**
```json
{ "name": "...", "email": "...", "password": "..." }
```
> password는 8자 이상

**Response 201**
```json
{ "ok": true, "user": { "id": "...", "name": "...", "email": "..." } }
```

**Error 400** — email 중복, 비밀번호 너무 짧음

---

### POST /api/auth/refresh/
인증 불필요

**Request**
```json
{ "refresh": "..." }
```

**Response 200**
```json
{ "access": "..." }
```

---

### GET /api/users/me/
인증 필요

**Response 200**
```json
{ "id": "...", "name": "...", "email": "...", "profile_label": "..." }
```

---

## 학습 세션

### POST /api/analysis/validate/
인증 필요

세션 생성 전 미리보기 검증용 엔드포인트. 아래 세션 생성(`POST /api/sessions/`)과 동일한 Request 구조를 사용.

**Request** — 세션 생성과 동일한 구조 (아래 참고)

**Response 200**
```json
{
  "ok": true,
  "preview": {
    "sessionDate": "YYYY-MM-DD",
    "book": "문제집명",
    "problemCount": 10,
    "participantCount": 3,
    "conceptTags": ["개념1", "개념2"]
  }
}
```

---

### POST /api/sessions/
인증 필요

**Request** (JSON body, 파일 업로드 아님)
```json
{
  "session_date": "YYYY-MM-DD",
  "book": "문제집명",
  "speakers": ["이름1", "이름2"],
  "problems": [
    {
      "problem_number": 1,
      "subject_area": "SQL 기본 및 활용",
      "concepts": ["개념1", "개념2"],
      "solution_summary": "풀이 요약",
      "participants": [
        {
          "name": "이름",
          "is_correct": true,
          "understanding": "이해",
          "concepts_covered": ["개념1"],
          "concepts_missed": ["개념2"],
          "errors": ["실수 내용"],
          "review_required": false
        }
      ]
    }
  ]
}
```

**Response 201**
```json
{ "ok": true, "session_id": "..." }
```

**Error 409** — 중복 세션 (같은 날짜·문제집 조합이 이미 존재)

---

### GET /api/sessions/
인증 필요

**Query Parameters**

| Parameter | Type | Description |
|---|---|---|
| search | string | 키워드 검색 |
| understanding | string | `high` 또는 `low` |
| date_from | string | `YYYY-MM-DD` |
| date_to | string | `YYYY-MM-DD` |

**Response 200**
```json
[
  {
    "id": "...",
    "session_date": "YYYY-MM-DD",
    "book": "문제집명",
    "speakers": ["이름1", "이름2"],
    "problem_count": 10,
    "average_understanding": 0.75,
    "review_required_count": 2,
    "created_at": "..."
  }
]
```

---

### GET /api/sessions/{session_id}/
인증 필요

**Response 200** — 세션 상세 (problems 배열 포함)
```json
{
  "id": "...",
  "session_date": "YYYY-MM-DD",
  "book": "문제집명",
  "speakers": ["이름1", "이름2"],
  "problems": [
    {
      "problem_number": 1,
      "subject_area": "SQL 기본 및 활용",
      "concepts": ["개념1", "개념2"],
      "solution_summary": "풀이 요약",
      "participants": [
        {
          "name": "이름",
          "is_correct": true,
          "understanding": "이해",
          "concepts_covered": ["개념1"],
          "concepts_missed": ["개념2"],
          "errors": ["실수 내용"],
          "review_required": false
        }
      ]
    }
  ],
  "created_at": "..."
}
```

---

### DELETE /api/sessions/{session_id}/
인증 필요

**Response 200**
```json
{ "ok": true }
```

---

## 분석

### GET /api/calendar/
인증 필요

**Query Parameters**

| Parameter | Type | Description |
|---|---|---|
| year | integer | 연도 (예: 2026) |
| month | integer | 월 (예: 6) |

**Response 200**
```json
{
  "year": 2026,
  "month": 6,
  "days": [
    { "date": "YYYY-MM-DD", "problemCount": 5, "hasSession": true }
  ],
  "weeklyProblemCount": 12,
  "monthlyProblemCount": 45,
  "studyStreak": 8
}
```

> **주의사항**
> - `weeklyProblemCount`: 오늘 기준 최근 7일간 문제 수 (조회한 month 기준이 아님)
> - `studyStreak`: 조회한 month 안에서 학습한 날의 수 (연속 일수가 아님)

---

### GET /api/study-comparison/
인증 필요

**Query Parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| session_id | string | 필수 | 비교할 세션 ID |

**Response 200**
```json
{
  "sessionId": "...",
  "book": "문제집명",
  "sessionDate": "YYYY-MM-DD",
  "participants": ["이름1", "이름2"],
  "problems": [
    {
      "problemNumber": 1,
      "concepts": ["개념1"],
      "participants": [
        {
          "name": "이름",
          "isCorrect": true,
          "understanding": "이해",
          "reviewRequired": false
        }
      ]
    }
  ]
}
```

---

### GET /api/dashboard/summary/
인증 필요

**Response 200**
```json
{
  "weeklyProblemCount": 12,
  "reviewRequiredCount": 5,
  "averageUnderstanding": 0.72,
  "studyStreak": 4,
  "recommendations": ["개념A", "개념B"],
  "recentSessions": [
    {
      "id": "...",
      "session_date": "YYYY-MM-DD",
      "book": "문제집명",
      "problem_count": 10
    }
  ]
}
```

---

### GET /api/weak-concepts/
인증 필요

**Response 200**
```json
[
  {
    "name": "개념명",
    "subject": "과목",
    "totalProblems": 10,
    "weakCountByParticipant": { "이름1": 3, "이름2": 2 },
    "scoreByParticipant": { "이름1": 0.4, "이름2": 0.6 },
    "averageScore": 0.5,
    "lastReviewDate": "YYYY-MM-DD",
    "recommend": true
  }
]
```

---

### GET /api/recommendations/review/
인증 필요

**Response 200**
```json
[
  {
    "concept": "개념명",
    "subject": "과목",
    "reason": "복습 권장 이유",
    "score": 0.35
  }
]
```

---

### GET /api/reports/growth/
인증 필요

**Query Parameters**

| Parameter | Type | Description |
|---|---|---|
| period | string | 예: `monthly` (echo만 됨 — 실제 날짜 필터링 없음, 전체 기간 데이터 반환) |

**Response 200**
```json
{
  "period": "monthly",
  "problemCount": 80,
  "averageUnderstanding": 0.68,
  "reviewRequiredCount": 15,
  "improvedConcepts": ["개념A", "개념B"],
  "stillWeakConcepts": ["개념C"],
  "trend": [
    { "label": "...", "score": 0.65 }
  ]
}
```

> **주의사항**: `period` 파라미터는 응답에 그대로 echo되지만, 실제 날짜 필터링은 수행되지 않음. 항상 전체 기간 데이터를 반환.

---

## 개념

### GET /api/concepts/
인증 필요

**Response 200**
```json
[
  {
    "id": "...",
    "name": "개념명",
    "subject": "과목",
    "summary": "개념 요약",
    "myUnderstanding": "이해",
    "reviewRecommended": false
  }
]
```

---

### GET /api/concepts/{concept_id}/
인증 필요

**Response 200**
```json
{
  "id": "...",
  "name": "개념명",
  "subject": "과목",
  "summary": "개념 요약",
  "frequentQuestionTypes": ["유형1", "유형2"],
  "confusingPoints": ["혼동 포인트1"],
  "wrongPatterns": ["오답 패턴1"],
  "relatedProblems": [
    {
      "sessionId": "...",
      "problemNumber": 3,
      "person": "이름",
      "understanding": "애매",
      "reviewRequired": true
    }
  ],
  "myUnderstanding": "애매",
  "reviewRecommended": true
}
```

> **주의사항**: `relatedProblems` 배열 각 항목에 `person` 필드 포함 (어느 참가자의 기록인지 식별)

---

## 오답노트

### GET /api/wrong-answers/
인증 필요

**Response 200**
```json
[
  {
    "id": "...",
    "sessionId": "...",
    "problemId": "...",
    "problemNumber": 5,
    "sessionDate": "YYYY-MM-DD",
    "book": "문제집명",
    "person": "이름",
    "concepts": ["개념1", "개념2"],
    "understanding": "모름",
    "missed": ["놓친 개념"],
    "errors": ["실수 내용"],
    "explanation": "풀이 설명",
    "isCorrect": false,
    "reviewRequired": true,
    "done": false
  }
]
```

---

### PATCH /api/wrong-answers/{wrong_answer_id}/
인증 필요

**URL 파라미터 형식**: `wrong_answer_id` = `{problem_id}::{name}` (예: `abc123::홍길동`)

**Request**
```json
{ "done": true }
```

**Response 200**
```json
{ "ok": true, "id": "...", "done": true }
```
