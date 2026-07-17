# subagent_wrapper_v1.md — 블록 4 속행 서브에이전트 wrapper 동결 (지시문 v13 블록0 각서1)

**목적:** chunk02~49의 병렬 서브에이전트 실행 아키텍처를 파일럿(chunk01 v3.13)과 동일하게 **고정**한다. 본 wrapper는 판정 내용을 일절 추가하지 않는 **순수 passthrough**다 — 모든 판정 규칙·측정 정의는 배치 payload(동결 `prompt_template_v2.1_batch.md` / `batch_assemble_v1.1.py`)에 있고, wrapper는 그 payload를 서브에이전트에 옮기는 것 외 어떤 판정 내용도 담지 않는다.

## 실행 아키텍처 (바이트 동일 고정)
- **입력 단위:** `batch_assemble_v1.1.py --map` 산출 각 배치 레코드 `{batch_id, dyad_ids, system, user}`.
- **디스패치:** 각 배치 → **claude-sonnet-5 서브에이전트 1개**. 동시 서브에이전트 수(병렬 규모)는 운영 재량.
- **서브에이전트 입력(★passthrough):** 배치의 `system` 필드를 서브에이전트 **system 프롬프트로 그대로**, 배치의 `user` 필드를 서브에이전트 **user 메시지로 그대로** 전달한다. **추가 문구·예시·재프레이밍·요약 일절 금지**(출력 형식 지시는 이미 `user` 말미 §3 출력 스펙에 포함됨).
- **서브에이전트 출력:** `prompt_template_v2.1_batch.md` §3 출력 스펙의 **JSON 배열만**(모든 dyad_id echo, 서술 금지).
- **부모 수집:** `{batch_id, model_string, raw_response}`를 raw 로그에 보존. 유효성·매칭·시도는 `generation_config_v2.md`(04c5bc64…) 규칙(echo 매칭·위치 금지·중복 echo invalid·필수 필드·dyad당 3회·최종 실패=NA).

## 규율
- 본 wrapper(passthrough 정의)는 chunk02~49 **전건 동일** 사용. **변경 = 새 각서 불가 — 중단·PI 보고만**(v13 블록0 각서1).
- model_string=claude-sonnet-5 상이 발생 = 즉시 전면 중단·PI 보고(위반 배치 무효).

## ★한계 투명 고지 (감사 추적)
파일럿(chunk01 v3.13)의 서브에이전트 **디스패치 원문 문자열은 별도 영속되지 않았다**(raw 로그는 응답만 보존). 다만 파일럿 보고서 §0은 "배치 `batch_assemble_v1.1.py` 산출 system/user를 파일에서 **그대로** 읽어 결정트리를 문자 그대로 적용, 창의적 개입 없음"으로 passthrough를 명시했다. 본 문서는 그 passthrough 아키텍처를 chunk02~49용으로 **정본 동결**한다 — 판정 내용이 payload에 100% 있으므로 디스패치 문구의 바이트 차이는 라벨을 좌우하지 않는다. **byte-exact 파일럿 wrapper가 필요하면 파일럿을 수행한 Sonnet 세션이 원문을 export해야 한다**(IJ 판단).
