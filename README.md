# 과제2 · 에이전트와 함께 만드는 URL 단축기

2026-2 **고급알고리즘**(SIT2001-01) 과제2 제출 저장소입니다.
2023128011 안세민

- 과제 안내: [lec-algorithm.github.io/lecture/article/hw2-2026](https://lec-algorithm.github.io/lecture/article/hw2-2026/)
- 수업 슬라이드: [lec-algorithm.github.io/lecture/slides/hw2-2026](https://lec-algorithm.github.io/lecture/slides/hw2-2026/)

Codespace 안의 에이전트에게 명세·계획·테스트·구현을 맡기고, 저는 요청을 쓰고 결과를 확인하는 방식으로
URL 단축기를 만들었습니다. 해시 테이블은 체이닝과 선형 탐지 두 가지로 직접 구현했고, 둘을 바꿔 끼워 비교했습니다.
`dict`, `set`, 내장 `hash()`는 쓰지 않았습니다.

## 구현한 것

| 파일 | 내용 |
| --- | --- |
| `src/base62.py` | base62 인코딩/디코딩. 글자 순서는 `0-9, a-z, A-Z`, `encode(0)`은 `"0"` |
| `src/hash_table.py` | 체이닝 해시 테이블. Horner 해시(`h = (h*31 + ord(c)) % m`), 새 노드는 버킷 앞에 붙임, 적재율 0.75를 넘으면 두 배로 확장 |
| `src/linear_probing.py` | 선형 탐지 해시 테이블. 같은 해시와 같은 메서드(`put`, `get`, `contains`, `remove`, `len`), 끝 칸 다음은 0번 칸, 삭제 표식과 재사용, 확장을 끄고 가득 차면 `OverflowError` |
| `src/shortener.py` | URL 단축기. `Shortener(table_factory=...)`로 두 테이블 중 하나를 고름 |
| `src/server.py` | 웹 서버. 단축, 리다이렉트(302), 잘못된 URL은 400, `/table`에서 테이블 내부 상태 확인 |
| `experiments/probe_experiment.py` | 6단계 체이닝 적재율 실험 → `results.csv`, `results.svg` |
| `experiments/compare_tables.py` | 체이닝과 선형 탐지 비교 실험 → `comparison_results.csv`, `comparison_results.svg` |
| `SPEC.md` · `PLAN.md` | 에이전트가 초안을 쓰고 제가 고친 명세와 구현 계획 |
| `.github/copilot-instructions.md` | 에이전트 규칙 파일 |

테스트는 `tests/`에 있고 38개가 모두 통과합니다. 단축기 테스트는 두 테이블에서 각각 돕니다.

## 실행

Codespaces 터미널(또는 아래 로컬 컨테이너)에서 실행합니다. 외부 라이브러리는 쓰지 않습니다.

| 하고 싶은 것 | 명령 |
| --- | --- |
| 테스트 | `make test` |
| 웹 서버 (체이닝, 포트 8000) | `make serve` |
| 웹 서버 (선형 탐지) | `make serve TABLE=linear` |
| 체이닝 적재율 실험 | `make experiment` |
| 두 해시 테이블 비교 | `make compare` |

`/table`에서는 체이닝은 버킷별 연결 리스트(화살표)를, 선형 탐지는 키마다 처음 계산한 칸부터 거쳐 간 칸(`7 → 0 → 1`)을
보여 주고, 각 키의 Horner 계산 과정을 펼쳐 볼 수 있습니다.

휴대폰으로 확인할 때는 포트 탭에서 8000을 Public으로 바꾸고 전달된 주소를 엽니다.
확인이 끝나면 서버를 중지하고 포트를 Private으로 되돌립니다.

`make compare`는 `experiments/`에 자동 요약 PDF도 만들지만, 제출 보고서는 직접 써서 LearnUs에 따로 올렸습니다.

## 실험 결과 요약

1000칸 고정, 확장 끔, 같은 키(시드 2026)로 적재율 α = 0.1~0.9를 측정했습니다. 괄호는 균등 해시 가정 이론값입니다.

| α | 체이닝 성공 | 체이닝 실패 | 선형 탐지 성공 | 선형 탐지 실패 |
| --- | --- | --- | --- | --- |
| 0.5 | 1.25 (1.25) | 0.51 (0.50) | 1.43 (1.50) | 2.53 (2.50) |
| 0.8 | 1.40 (1.40) | 0.81 (0.80) | 3.65 (3.00) | 13.96 (13.00) |
| 0.9 | 1.44 (1.45) | 0.91 (0.90) | 6.95 (5.50) | 68.19 (50.50) |

0.5까지는 비슷하지만, 선형 탐지는 1차 군집 때문에 적재율이 높아질수록 실패 탐색이 급격히 늘어납니다.
전체 결과는 `experiments/comparison_results.csv`, 그래프는 `experiments/comparison_results.svg`에 있습니다.

## 작업 방식

- 단계마다 이슈(#1~#8)를 만들고 `feature/<번호>-<이름>` 브랜치에서 작업한 뒤 `develop`을 거쳐 `main`에 머지했습니다.
- 각 이슈 댓글에 제가 고친 것, 확인한 것, 에이전트가 틀린 곳을 남겼습니다.
  - #1: 채팅 방식과 에이전트 방식에서 각각 손으로 한 일
  - #8: 에이전트가 틀린 곳 두 가지(단축기 테스트가 선형 탐지로 거의 돌지 않던 것, `/table` 테스트가 탐색 순서를 확인하지 않던 것)와 일부러 코드를 망가뜨려 확인한 결과
- 사용 AI: Claude

## 로컬에서 하기

```sh
git clone https://github.com/ramzz527/algorithms-hw2.git
cd algorithms-hw2
docker compose up -d
docker compose exec lab bash
```

**이후 모든 `docker compose` 명령은 이 폴더에서 칩니다.**
