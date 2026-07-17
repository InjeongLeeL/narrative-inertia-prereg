# prompt_template_v2.0_batch.md — 설계 E 사전등록 수정안 v3.12 §정정4-1(1) 동결 산출물

**역할:** 대리라벨 **배치 분류**용 프롬프트 명세(응답당 50건). 실제 조립은 `batch_assemble_v1.py`가 수행하며, 본 문서는 그 동결 상수(SYSTEM·약식 rubric·출력형식)를 문자 그대로 수록한다.
**측정 정의:** 코드북 v1.4 준거. **SYSTEM 프롬프트는 v1.6(phase0b_render_prompts_v16.py) SYSTEM과 바이트 동일**(코드북 핵심·V 비유래). 5범주·in/out 매핑 불변(v3.11 §1.3·§3.2).

## ★V 유래 few-shot 앵커 승계 여부 공시: **미승계(전량 미승계)**

v1.6 few-shot 앵커 14건(v7 FP 교정 8 + v1.6 역방향 6, 전부 V 실제 초록 유래)은 **v2.0 배치 템플릿에 승계하지 않는다.** 사유 2가지:

1. **배치 컴팩트성:** 앵커 14건(장문 실초록 포함)을 매 배치에 반복하면 배치당 토큰이 폭증해 50건 일괄 분류의 효율이 무너진다.
2. **V 누출 차단:** 앵커는 V-dev 285 유래이므로, 승계 시 §4의 3항 V-dev sanity(P/R/AC1)에서 train/test 중복이 된다. 미승계로 원천 차단(그럼에도 sanity 주 지표는 앵커 dyad 제외본 — 이중 안전).

**보존:** 앵커가 인코딩하던 코드북 판정 논리(삭제 테스트·종착 술어 (i)~(iv)·false-friend·comparative/passing·재정 E/F/G/H/I·wrong_referent 7항)는 **약식 rubric 본문에 조문 형태로 보존**된다(예시 실초록만 제거, 판정 기준은 동일). 측정 정의 동일성은 코드북 v1.4 준거 명시 + 본 템플릿 동결·공시로 담보(v3.12 §4-3).

---

## 1. SYSTEM 프롬프트 (v1.6 바이트 동일)

```
당신은 혁신정책·과학기술학 서지 스크리닝 전문가다. 논문 초록에서 '특정 국가의 혁신(시스템·정책·활동·성과)이 실제 논의 대상인지' 판정한다. 지배 규칙(삭제 테스트): 그 국가의 혁신·기술·경제 역량 진술을 삭제해도 논문 주장이 그대로면, 그 국가는 논의 대상이 아니다. 논의 수준·시점은 성립과 무관. 확신 없으면 낮은 쪽(불성립). 지정 JSON으로만 답하고 초록에 없는 정보 추측 금지.
```

## 2. 약식 결정트리 + 코드북 rubric (배치 user 본문 상단, 전문)

```
[약식 결정트리 — 각 항목에 다음 3단만 적용]
STEP1 referent(7항): 매칭 표현이 해당 국가(의 혁신)를 실제 가리키나? 비지시면 wrong_referent. 비지시 목록: 북한/디아스포라/대륙형용사(American=대륙)/대명사(소문자 us)/언어·질병명/통화·단위토큰(US$·KRW·¥·€)/국가명 포함 고유명(German Shepherd 등). 단 해당국 영토·관할(US Virgin Islands)은 wrong 아님(→dso). 과거·역사는 wrong 아님.
STEP2 역량진술(종착 술어 테스트): 종착 술어의 최종 귀속이 (i)혁신·기술 산출/역량 (ii)산업·기업 경쟁력 (iii)경제 성과·제도(혁신·기술·산업 연계분에 限) → in / (iv)서비스 전달·교육·복지·보건·행정 거버넌스·외교·순수 거시안정화(재정승수·통화정책·환율) → out. 연계 예외: 비역량 표현도 최종 귀속이 (i)~(iii)이면 in. false-friend: 계량모형 innovation(s)/innovation disturbance=VAR/SVAR 통계 충격·교란항 → 혁신 담론 아님. 역량진술 없으면: 국가 실체(기업·기관·지역·문서·시계열·응답자)가 수집·분석 대상=data_source_only(도메인 무관) / 장소·배경·소속·주최=passing_mention.
STEP3 역할(in인 경우): 주 대상=substantive / 비교준거 개별 귀속 완결명제=comparative_referent. 이름 나열·집합 선택 수식·얇은 1~2문장 벤치마크=passing_mention(out). 설계된 co-equal 비교=substantive.
[재정 요지] E: 순수 거시안정화 out. G: 정책수단 혁신(policy innovation)·규제 라벨=거버넌스(iv) out. F: 종착 술어는 in/out만 결정, out 후 범주는 역할로만('(iv)이므로 passing' 논법 금지). H: 국가명 포함 고유명 wrong. I: 다국 비교는 국가 수 아닌 설계(co-equal=substantive / 순위·나열 개별귀속=comparative). 매핑/순위 데이터(계량서지·특허·패널)에서 국가가 측정·순위 단위면 개별 수치 언급돼도 data_source_only. KR=대한민국(남한).
```

## 3. 배치 출력 형식 명세 (전문)

```
[출력 — 배치 JSON 배열만]
판정 대상 목록의 **모든** 항목에 대해 아래 스키마 객체를 원소로 갖는 JSON 배열 하나로만 답한다. 서술·코드펜스 금지.
각 원소 = {"dyad_id":"<입력 그대로 echo>","paper_id":"","country":"","category":"<substantive|comparative_referent|data_source_only|passing_mention|wrong_referent>","dyad_status":"<in|out>","role":"","confidence":<0~1>,"rationale":"<한 구절 태그>","referent_note":"<간단>"}
정합: in ⇔ category∈{substantive,comparative_referent}. **dyad_id는 반드시 입력값을 그대로 echo**(위치 아닌 dyad_id로 매칭). 목록의 모든 dyad_id를 빠짐없이 1회씩 포함.
```

## 4. 배치 user 조립 구조 (batch_assemble_v1.py)

user = 약식 rubric(§2) + `[판정 대상 목록 (N건)]` + N개 항목 블록 + 출력 형식(§3). 각 항목 블록:

```
[i] dyad_id=<echo용 id> | 판정대상국=<COUNTRY_FULL(+KR flag_kr_dyad_only=1 시 남한 한정)>
제목:{Title} | 저널:{Journal} | 연도:{Year} | 키워드:{Keywords}
초록:{Abstract}
{초록<100단어 시 근거제한 고지}<flags>{플래그 힌트 또는 '특이 플래그 없음.'}</flags>
```

배치 구성·유효성·시도·raw 보존 규칙은 v3.12 §4-2 및 generation_config_v2.md 참조. dyad_id echo 필수·위치 매칭 금지·중복 echo 무효·고정 크기 50(canonical 오름차순).
