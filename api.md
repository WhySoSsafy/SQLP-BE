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

  5. 학습 세션 생성

  POST /api/sessions/

  요청은 검증 API와 동일한 원본 JSON.

  응답:

  {
    "ok": true,
    "session_id": "2026-06-13-sqlp-실전문제-1"
  }

  중복 응답:

  {
    "ok": false,
    "code": "DUPLICATE_SESSION",
    "message": "같은 날짜, 문제집명, 문제번호 구성을 가진 학습 세션이 이미 저장되어 있습니다."
  }

  6. 학습 세션 목록

  GET /api/sessions/

  쿼리 옵션:

  ?search=SQLP
  ?understanding=high
  ?date_from=2026-06-01
  ?date_to=2026-06-30

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

  15. 스터디원 비교

  GET /api/study-comparison/

  쿼리:

  ?session_id=2026-06-13-sqlp-실전문제-1-2

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
        "understanding": "애매",
        "reviewRequired": true
      }
    ],
    "myUnderstanding": 40,
    "reviewRecommended": true
  }

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

  쿼리:

  ?period=monthly

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