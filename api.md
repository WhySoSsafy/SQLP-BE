공통
  Base URL 예시:

  /api

  공통 응답 에러 형식:

  {
    "ok": false,
    "code": "VALIDATION_ERROR",
    "message": "입력값이 올바르지 않습니다.",
    "errors": [
      {
        "path": "$.problems[0].subject_area",
        "message": "허용되지 않는 과목입니다."
      }
    ]
  }

  인증 헤더:
  로그인/회원가입을 제외한 모든 API에 Authorization 헤더 필요.

  Authorization: Bearer <access_token>

  예시:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

  헤더 누락 또는 만료 토큰 사용 시:
  HTTP 401
  {
    "ok": false,
    "code": "not_authenticated",
    "message": "자격 인증데이터(authentication credentials)가 제공되지 않았습니다."
  }

  인증 불필요 엔드포인트:
  - POST /api/auth/login/
  - POST /api/auth/register/
  - POST /api/auth/refresh/

  이해도(understanding) 허용 값:
  - "이해": 완전히 이해함 (점수 100)
  - "애매": 이해했지만 불확실 (점수 50)
  - "모름": 이해하지 못함 (점수 0)

  평균 이해도(average_understanding)는 위 점수의 평균값 (0~100).

  JSON 데이터 전송 방식:
  AI 분석 결과 JSON은 파일 업로드가 아닌 request body로 직접 전송.

  Content-Type: application/json
  Body: { ...세션 데이터... }

  파일 업로드(multipart/form-data)는 지원하지 않음.
  프론트엔드에서 JSON 파일을 읽은 경우, 파일 객체가 아닌 파싱된 JSON 객체를 body로 전송.

  1. 로그인

  POST /api/auth/login/

  요청:

  {
    "email": "seun@example.com",
    "password": "password123"
  }

  응답:

  {
    "access": "jwt-access-token",
    "refresh": "jwt-refresh-token",
    "user": {
      "id": 1,
      "name": "세은",
      "email": "seun@example.com"
    }
  }

  상태 코드: 200 OK

  에러 응답 (잘못된 자격증명):
  HTTP 401
  {
    "ok": false,
    "code": "no_active_account",
    "message": "No active account found with the given credentials"
  }

  에러 응답 (필드 누락):
  HTTP 400
  {
    "ok": false,
    "code": "VALIDATION_ERROR",
    "message": "입력값이 올바르지 않습니다.",
    "errors": [
      { "path": "$.email", "message": "이 필드는 필수 항목입니다." }
    ]
  }

  토큰 유효기간:
  - access token: 1시간 (만료 후 refresh 엔드포인트로 갱신)
  - refresh token: 7일

  토큰 갱신:
  POST /api/auth/refresh/

  요청:

  {
    "refresh": "jwt-refresh-token"
  }

  응답:

  {
    "access": "new-jwt-access-token"
  }

  2. 회원가입

  POST /api/auth/register/

  요청:

  {
    "name": "세은",
    "email": "seun@example.com",
    "password": "password123"
  }

  응답:

  {
    "ok": true,
    "user": {
      "id": 1,
      "name": "세은",
      "email": "seun@example.com"
    }
  }

  상태 코드: 201 Created

  에러 응답 (이메일 중복):
  HTTP 400
  {
    "ok": false,
    "code": "VALIDATION_ERROR",
    "message": "입력값이 올바르지 않습니다.",
    "errors": [
      { "path": "$.email", "message": "이 필드를 가진 accounts user가(이) 이미 존재합니다." }
    ]
  }

  에러 응답 (비밀번호 8자 미만):
  HTTP 400
  {
    "ok": false,
    "code": "VALIDATION_ERROR",
    "message": "입력값이 올바르지 않습니다.",
    "errors": [
      { "path": "$.password", "message": "이 필드의 글자 수가 8 이상인지 확인하십시오." }
    ]
  }

  3. 내 정보 조회

  GET /api/users/me/

  응답:

  {
    "id": 1,
    "name": "세은",
    "email": "seun@example.com",
    "profile_label": "SQLP 준비 중"
  }

  4. AI 분석 JSON 검증

  POST /api/analysis/validate/

  인증: 필요 (Authorization: Bearer <access_token>)
  상태 코드: 200 OK

  요청:

  {
    "session_date": "2026-06-13",
    "book": "SQLP 실전문제",
    "speakers": ["세은", "수철"],
    "problems": [
      {
        "problem_number": 1,
        "subject_area": "SQL 기본 및 활용",
        "concepts": ["JOIN", "OUTER JOIN"],
        "solution_summary": "OUTER JOIN 기준 테이블을 묻는 문제",
        "participants": [
          {
            "name": "세은",
            "is_correct": true,
            "understanding": "애매",
            "concepts_covered": ["OUTER JOIN"],
            "concepts_missed": ["NULL 처리"],
            "errors": ["기준 테이블 방향을 혼동함"],
            "review_required": true
          }
        ]
      }
    ]
  }

  성공 응답:

  {
    "ok": true,
    "preview": {
      "sessionDate": "2026-06-13",
      "book": "SQLP 실전문제",
      "problemCount": 1,
      "participantCount": 2,
      "conceptTags": ["JOIN", "OUTER JOIN"]
    }
  }

  에러 응답 (필수 필드 누락 또는 값 오류):
  HTTP 400
  {
    "ok": false,
    "code": "VALIDATION_ERROR",
    "message": "입력값이 올바르지 않습니다.",
    "errors": [
      { "path": "$.problems[0].subject_area", "message": "허용되지 않는 과목입니다." }
    ]
  }

  5. 학습 세션 생성

  POST /api/sessions/

  인증: 필요 (Authorization: Bearer <access_token>)
  상태 코드: 201 Created

  요청은 검증 API와 동일한 원본 JSON.

  성공 응답:

  {
    "ok": true,
    "session_id": "2026-06-13-sqlp-실전문제-1"
  }

  중복 응답:

  HTTP 409
  {
    "ok": false,
    "code": "DUPLICATE_SESSION",
    "message": "같은 날짜, 문제집명, 문제번호 구성을 가진 학습 세션이 이미 저장되어 있습니다."
  }

  에러 응답 (유효성 오류):

  HTTP 400
  {
    "ok": false,
    "code": "VALIDATION_ERROR",
    "message": "입력값이 올바르지 않습니다.",
    "errors": [...]
  }

  6. 학습 세션 목록

  GET /api/sessions/

  인증: 필요 (Authorization: Bearer <access_token>)
  상태 코드: 200 OK

  쿼리 파라미터 상세:
  - search: book 필드에 부분 일치 (대소문자 무관)
  - understanding=high: average_understanding >= 70인 세션만
  - understanding=low: average_understanding < 50인 세션만
  - date_from / date_to: YYYY-MM-DD 형식. 잘못된 형식 시 HTTP 400

  검증 완료: 실제 학습 기록 기반 응답 정상 동작 확인 (2026-06-22)

  응답:

  [
    {
      "id": "2026-06-13-sqlp-실전문제-1-2",
      "session_date": "2026-06-13",
      "book": "SQLP 실전문제",
      "speakers": ["세은", "수철"],
      "problem_count": 2,
      "average_understanding": 50,
      "review_required_count": 2,
      "created_at": "2026-06-13T09:00:00Z"
    }
  ]

  7. 학습 세션 상세

  GET /api/sessions/{session_id}/

  응답:

  {
    "id": "2026-06-13-sqlp-실전문제-1-2",
    "session_date": "2026-06-13",
    "book": "SQLP 실전문제",
    "speakers": ["세은", "수철"],
    "created_at": "2026-06-13T09:00:00Z",
    "problems": [
      {
        "id": "2026-06-13-sqlp-실전문제-1-2-p1",
        "problem_number": 1,
        "subject_area": "SQL 기본 및 활용",
        "concepts": ["JOIN", "OUTER JOIN", "NULL"],
        "solution_summary": "OUTER JOIN에서 기준 테이블의 데이터 보존 여부를 묻는 문제",
        "participants": [
          {
            "name": "세은",
            "is_correct": true,
            "understanding": "애매",
            "concepts_covered": ["OUTER JOIN"],
            "concepts_missed": ["NULL 처리"],
            "errors": ["기준 테이블의 방향을 일부 혼동함"],
            "review_required": true
          }
        ]
      }
    ]
  }

  8. 학습 세션 삭제

  DELETE /api/sessions/{session_id}/

  응답:

  {
    "ok": true
  }

  9. 홈 대시보드 요약

  GET /api/dashboard/summary/

  응답:

  {
    "weeklyProblemCount": 3,
    "reviewRequiredCount": 3,
    "averageUnderstanding": 60,
    "studyStreak": 1,
    "recommendations": [
      {
        "concept": "OUTER JOIN",
        "subject": "SQL 기본 및 활용",
        "reason": "모름/오답 반복으로 우선 복습이 필요해요.",
        "score": 40
      }
    ],
    "recentSessions": [
      {
        "id": "2026-06-13-sqlp-실전문제-1-2",
        "date": "2026-06-13",
        "book": "SQLP 실전문제",
        "problemCount": 2,
        "averageUnderstanding": 50
      }
    ]
  }

  10. 복습 추천 목록

  GET /api/recommendations/review/

  응답:

  [
    {
      "concept": "OUTER JOIN",
      "subject": "SQL 기본 및 활용",
      "reason": "모름/오답 반복으로 우선 복습이 필요해요.",
      "score": 40
    }
  ]

  11. 취약 개념 목록

  GET /api/weak-concepts/

  응답:

  [
    {
      "name": "OUTER JOIN",
      "subject": "SQL 기본 및 활용",
      "totalProblems": 1,
      "weakCountByParticipant": {
        "세은": 1,
        "수철": 1
      },
      "scoreByParticipant": {
        "세은": 60,
        "수철": 20
      },
      "averageScore": 40,
      "lastReviewDate": "2026-06-13",
      "recommend": true
    }
  ]

  12. 오답노트 목록

  GET /api/wrong-answers/

  응답:

  [
    {
      "id": "session-p1-세은",
      "sessionId": "2026-06-13-sqlp-실전문제-1-2",
      "problemId": "2026-06-13-sqlp-실전문제-1-2-p1",
      "problemNumber": 1,
      "sessionDate": "2026-06-13",
      "book": "SQLP 실전문제",
      "person": "세은",
      "concepts": ["JOIN", "OUTER JOIN"],
      "understanding": "애매",
      "missed": ["NULL 처리"],
      "errors": ["기준 테이블의 방향을 일부 혼동함"],
      "explanation": "OUTER JOIN에서 기준 테이블의 데이터 보존 여부를 묻는 문제",
      "isCorrect": true,
      "reviewRequired": true,
      "done": false
    }
  ]

  13. 오답노트 복습 완료 처리

  PATCH /api/wrong-answers/{wrong_answer_id}/

  요청:

  {
    "done": true
  }

  응답:

  {
    "ok": true,
    "id": "session-p1-세은",
    "done": true
  }

  14. 학습 캘린더

  GET /api/calendar/

  인증: 필요 (Authorization: Bearer <access_token>)
  상태 코드: 200 OK

  쿼리:

  ?year=2026&month=6

  응답:

  {
    "year": 2026,
    "month": 6,
    "days": [
      {
        "date": "2026-06-13",
        "problemCount": 2,
        "averageUnderstanding": 50,
        "mainConcepts": ["OUTER JOIN", "실행계획"],
        "reviewRequiredCount": 2
      }
    ],
    "weeklyProblemCount": 3,
    "monthlyProblemCount": 3,
    "studyStreak": 1
  }

  필드 상세:
  - weeklyProblemCount: 오늘 기준 최근 7일간 문제 수 (조회 월 기준 아님)
  - studyStreak: 조회 월에서 학습한 날의 수 (연속일 계산 아님)
  - mainConcepts: 해당 날짜에서 가장 많이 등장한 개념 최대 3개

  검증 완료: 실제 DB 기반 응답 정상 동작 확인 (2026-06-22)

  15. 스터디원 비교

  GET /api/study-comparison/

  인증: 필요 (Authorization: Bearer <access_token>)
  상태 코드: 200 OK

  쿼리:

  ?session_id=2026-06-13-sqlp-실전문제-1-2

  session_id 파라미터 필수. 누락 시:
  HTTP 400
  {
    "ok": false,
    "code": "VALIDATION_ERROR",
    "message": "입력값이 올바르지 않습니다.",
    "errors": [
      {
        "path": "$.session_id",
        "message": "필수 값입니다."
      }
    ]
  }

  세션 없을 시: HTTP 404

  weakConcepts 산출 기준: concepts_missed 목록 + 오답/복습필요 문제의 개념명

  검증 완료: 응답 형태 프론트 요구사항 충족 확인 (2026-06-22)

  응답:

  {
    "sessionId": "2026-06-13-sqlp-실전문제-1-2",
    "book": "SQLP 실전문제",
    "sessionDate": "2026-06-13",
    "participants": [
      {
        "name": "세은",
        "averageUnderstanding": 60,
        "correctCount": 1,
        "reviewRequiredCount": 2,
        "weakConcepts": ["NULL 처리", "실행계획"]
      },
      {
        "name": "수철",
        "averageUnderstanding": 60,
        "correctCount": 1,
        "reviewRequiredCount": 1,
        "weakConcepts": ["OUTER JOIN"]
      }
    ],
    "problems": [
      {
        "problemNumber": 1,
        "concepts": ["OUTER JOIN", "NULL"],
        "participants": [
          {
            "name": "세은",
            "isCorrect": true,
            "understanding": "애매",
            "reviewRequired": true
          },
          {
            "name": "수철",
            "isCorrect": false,
            "understanding": "모름",
            "reviewRequired": true
          }
        ]
      }
    ]
  }

  16. 개념 요약 목록

  GET /api/concepts/

  응답:

  [
    {
      "id": 1,
      "name": "OUTER JOIN",
      "subject": "SQL 기본 및 활용",
      "summary": "OUTER JOIN은 기준 테이블의 행을 보존하면서 다른 테이블과 조인하는 방식입니다.",
      "myUnderstanding": 40,
      "reviewRecommended": true
    }
  ]

  17. 개념 요약 상세

  GET /api/concepts/{concept_id}/

  응답:

  {
    "id": 1,
    "name": "OUTER JOIN",
    "subject": "SQL 기본 및 활용",
    "summary": "OUTER JOIN은 기준 테이블의 행을 보존하면서 다른 테이블과 조인하는 방식입니다.",
    "frequentQuestionTypes": [
      "LEFT OUTER JOIN 결과 예측",
      "WHERE 조건 적용 후 NULL 처리"
    ],
    "confusingPoints": [
      "ON 조건과 WHERE 조건의 적용 순서",
      "NULL 비교 시 = NULL이 아니라 IS NULL 사용"
    ],
    "wrongPatterns": [
      "기준 테이블 방향을 반대로 이해함"
    ],
    "relatedProblems": [
      {
        "sessionId": "2026-06-13-sqlp-실전문제-1-2",
        "problemNumber": 1,
        "person": "세은",
        "understanding": "애매",
        "reviewRequired": true
      }
    ],
    "myUnderstanding": 40,
    "reviewRecommended": true
  }

  인증: 필요 (Authorization: Bearer <access_token>)
  상태 코드: 200 OK

  개념 없을 시: HTTP 404

  검증 완료: relatedProblems에 person 필드 포함 확인 — 스펙 수정 완료 (2026-06-22)

  18. 문제 난이도/주제 분석 등록

  POST /api/problem-analysis/

  요청:

  {
    "book": "SQLP 실전문제",
    "problems": [
      {
        "problem_number": 1,
        "subject_area": "SQL 기본 및 활용",
        "concepts": ["JOIN", "OUTER JOIN"],
        "estimated_difficulty": "중",
        "frequency": "높음",
        "priority": 1
      }
    ]
  }

  응답:

  {
    "ok": true,
    "created_count": 1
  }

  19. 문제 난이도/주제 분석 목록

  GET /api/problem-analysis/

  응답:

  [
    {
      "id": 1,
      "book": "SQLP 실전문제",
      "problem_number": 1,
      "subject_area": "SQL 기본 및 활용",
      "concepts": ["JOIN", "OUTER JOIN"],
      "estimated_difficulty": "중",
      "frequency": "높음",
      "priority": 1
    }
  ]

  20. 통계 리포트

  GET /api/reports/growth/

  인증: 필요 (Authorization: Bearer <access_token>)
  상태 코드: 200 OK

  쿼리:

  ?period=monthly

  기간 파라미터 동작:
  - period 파라미터는 응답에 echo되기만 하고 실제 날짜 필터링은 없습니다.
  - 항상 그룹 전체 기간 데이터를 반환합니다 (period 값과 무관하게).
  - 예: "monthly"를 전달하면 응답에 "period": "monthly"로 포함되지만, 데이터는 모든 시간대를 포함합니다.

  응답 데이터 설명:
  - improvedConcepts: averageScore >= 70인 개념 목록 (성장한 개념)
  - stillWeakConcepts: averageScore < 50인 개념 목록 (여전히 약한 개념)

  응답:

  {
    "period": "monthly",
    "problemCount": 42,
    "averageUnderstanding": 68,
    "reviewRequiredCount": 11,
    "improvedConcepts": ["GROUP BY", "정규화"],
    "stillWeakConcepts": ["OUTER JOIN", "실행계획"],
    "trend": [
      {
        "date": "2026-06-01",
        "averageUnderstanding": 52
      },
      {
        "date": "2026-06-15",
        "averageUnderstanding": 68
      }
    ]
  }

  검증 완료: 프론트 성장 리포트 화면에 필요한 데이터 반환 확인 (2026-06-22)