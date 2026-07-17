# generation_config_v2.md — 설계 E 사전등록 수정안 v3.12 §정정4-1(3) 동결 산출물

대리라벨 **배치 생성**(§4-2)의 시도·유효성·모델 규약. v3.11 generation_config_v1.md(62e63932…)는 무변경 존치 — 본 v2가 배치 경로에서 §1.3 판정 심도·모델 고정 대상을 supersede(그 외 불변). 동결 후 수정 = 새 수정안.

## 1. 생성 모델 (v3.12 정정 3)
- 전 49청크 대리라벨 = **Sonnet 계열 단일 모델** 고정. "전 청크 model_string 동일" 규칙(v3.11 §1.3)은 불변 — 고정 대상만 Opus→Sonnet.
- **정확 model_string은 파일럿(§4) 첫 유효 응답에서 실측·확정**하고 decision log에 기재. 그 값이 이후 전 청크 동일성 기준값. 상이 발생 = 즉시 중단·PI 보고(위반 청크 무효).
- Cowork 환경 제어 불가 파라미터(temperature 등) = "제어 불가·기본값" 명기.

## 2. 배치 구성 (결정적, v3.12 §4-2)
- 청크(500) 내 dyad_id **canonical 오름차순 · 고정 크기 50** 분할(마지막 잔여 배치 <50 허용). 난수·재량 없음(동일 입력→동일 배치). 조립 = `batch_assemble_v1.py`.
- **각 배치 완료 즉시 저장 · progress 갱신 · 부분 봉인**(v3.11 §3.1 운영 골격의 배치 단위 적용 — 배치=크래시 안전 체크포인트). 청크(500) 단위 병합·봉인은 유지.

## 3. dyad 단위 유효성 (시도 계수 단위 = dyad, v3.11 불변)
배치 응답 내 각 dyad에 대해:
- **파싱 유효성 4조건(v3.11 §1.3):** category ∈ {substantive, comparative_referent, data_source_only, passing_mention, wrong_referent} 외 = invalid; category–status 정합(in={substantive, comparative_referent}) 위반 = invalid; 필수 필드 누락 = invalid; confidence ∉ [0,1] = invalid.
- **echo 무결성:** echo 누락(요청 dyad가 응답에 없음) = invalid; 중복 echo(동일 dyad_id ≥2회) = invalid(응답 간 선택 금지의 배치 확장); 미요청 id echo = 해당 판정 무시·기록만.
- **매칭 = echo된 dyad_id 기준. 위치(순서) 기준 매칭 금지.**
- invalid 아닌 dyad = **채택**(배치 전체 재시도 금지 — 유효분 보존).

## 4. 시도 규칙 (dyad당 총 3회, v3.11 불변)
- 최초 1회 + 재시도 최대 2회. **재시도 = 실패 dyad만 수집 → canonical 오름차순·고정 크기 50 재배치** → 후속 시도.
- 3회 모두 실패(또는 최종 invalid) = NA. NA 확정은 **병합 시점**(v3.11 §3.3): surrogate_analysis_category=data_source_only, status=out, **imputed=1**.
- `attempt_count` = 해당 dyad 실제 시도 수(1~3).

## 5. raw 보존 · 출력 스키마
- 전 배치 원응답 raw + **batch_id ↔ dyad_id 매핑 로그** 보존(v3.11 raw 보존 원칙의 배치 확장). `raw_log_pointer`로 참조.
- 출력 스키마 = v3.11 §3.2 전 필드 불변: `dyad_id, paper_id, country, surrogate_raw_category, surrogate_analysis_category, surrogate_analysis_status, confidence, role, rationale, referent_note, parse_status, attempt_count, imputed, raw_log_pointer, chunk, ts, model_string`.

## 6. rationale (v3.12 정정 1)
- 한 구절 태그로 충분(예: "dso: 특허 데이터원", "subst: 국가 혁신시스템"). 전문 서술 불요. 측정 정의(5범주·in/out·코드북 v1.4)는 동일.
