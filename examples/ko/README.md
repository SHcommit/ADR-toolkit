# ADR Toolkit 예제 가이드 (한국어)

이 디렉터리는 ADR Toolkit을 실제 프로젝트에 적용할 때 참고할 수 있는 유즈케이스별 한국어 실무 예시 가이드를 제공합니다.

## 예제 목록

| 예제 문서 | 주요 유즈케이스 | 핵심 CLI 명령어 |
|---|---|---|
| [`basic-usage.md`](basic-usage.md) | **기본 사용법**: 저장소 초기화, 의사결정 중요도 평가, ADR 작성 및 색인 생성 | `init`, `significance`, `create`, `index` |
| [`check-constraints.md`](check-constraints.md) | **기계적 제약조건 검증**: ADR 내 `forbidden_import` 규칙 작성, diff 위반 감지, 코드 수정 및 예외 등록 | `check`, `exception` |
| [`graph-visualization.md`](graph-visualization.md) | **아키텍처 진화 및 관계 그래프**: 대체된 ADR 마킹 및 Mermaid (`.mmd`) / SVG (`.svg`) 의사결정 그래프 생성 | `supersede`, `graph` |
| [`multilingual-adr.md`](multilingual-adr.md) | **다국어 저장소 지원**: 한국어 제목/본문(`--locale ko`) 작성과 이식성 있는 ASCII 파일명 슬러그(`--slug`) 활용 | `init --locale`, `create --slug` |

## 검증 및 자동화 파이프라인

모든 예제 문서의 CLI 명령어와 출력 결과는 `adr.py` 스크립트를 통해 자동으로 검증되며, CLI 로직 변경 시 자동으로 업데이트할 수 있습니다.

```bash
# 예제 명령어 동작 검증 실행
python3 scripts/verify_examples.py --check

# CLI 출력 변경 시 예제 출력 자동 업데이트
python3 scripts/verify_examples.py --update
```

영어 버전 문서는 [`../`](../) 디렉터리에서 확인할 수 있습니다.
