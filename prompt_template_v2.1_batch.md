# prompt_template_v2.1_batch.md — 설계 E 사전등록 수정안 v3.13 §3 동결 산출물

**역할:** 대리라벨 **배치 분류**용 프롬프트 명세(응답당 50건). v2.0 + **dso 경계 압축 반례/경계 앵커 재도입.** 실제 조립 = `batch_assemble_v1.1.py`, 본 문서는 그 동결 상수를 문자 그대로 수록.
**측정 정의:** 코드북 v1.4 준거. **SYSTEM은 v1.6(phase0b_render_prompts_v16.py) SYSTEM과 바이트 동일.** 5범주·in/out 매핑·출력 스키마·배치 세칙(§4-2) 불변 — v2.0 대비 **약식 rubric의 경계 앵커 블록만 추가.**

## ★V 유래 앵커 승계 공시: **일부 승계 — 8건 (원 14건 내 압축 조달)**

v3.12 v2.0은 앵커 **전량 미승계**였으나, chunk01·V-dev 실측에서 dso 경계 붕괴(gold dso 190 vs surrogate 48) 관측(v3.13 촉발) → **원 V앵커 14건 내에서 압축본 8건 재도입.** 구성 = dso 반례 5 + thin-benchmark passing 1 + 경계 보존 in 2.

**앵커별 원 pilot_id 매핑(감사 추적 — 전건 원 14건 내, 신규 조달 0):**

| # | 압축 앵커(요지) | 원 pilot_id | 국가 | gold 범주 |
|---|---|---|---|---|
| 1 | 미국 특허·계량서지 기술역량 지표화(NFM) | V141 | US | data_source_only |
| 2 | OECD 재생에너지 패널 미국=혁신 1위(순위) | V210 | US | data_source_only |
| 3 | 미국·독일·한국·스웨덴 디지털경제 시가총액 측정 | V013 | DE | data_source_only |
| 4 | 미국 모터스포츠 클러스터 형성 사례 | V154 | US | data_source_only |
| 5 | 한국 R&D 보조금 기업 추가성 패널 | V137 | KR | data_source_only |
| 6 | 이탈리아 R&D 논문 미국=한 줄 벤치마크 | V167 | US | passing_mention |
| 7 | 일본 편의점 발주=일본식 경쟁무기 | V020 | JP | substantive |
| 8 | 미국=brain circulation 개별귀속 비교준거 | V012 | US | comparative_referent |

- **V-dev 재측정 주 지표 제외집합 = 원 14건 전체(V012·V013·V020·V042·V083·V097·V101·V137·V141·V154·V167·V206·V210·V273)로 양 라운드 고정**(n=271). 재도입 8건은 그 부분집합이므로 제외집합 불변 — 라운드 간 비교가능성 유지(v3.13 정정1).
- V는 모집단(24,149)에서 paper 수준 제외 → 본 실행 사용 가능, sanity 주 지표에서만 무조건 제외(학습-평가 오염 원천 차단).
- 압축본은 실초록 전문이 아닌 판정 요지 1행(배치 컴팩트성).

---

## 1. SYSTEM 프롬프트 (v1.6 바이트 동일)

```
당신은 혁신정책·과학기술학 서지 스크리닝 전문가다. 논문 초록에서 '특정 국가의 혁신(시스템·정책·활동·성과)이 실제 논의 대상인지' 판정한다. 지배 규칙(삭제 테스트): 그 국가의 혁신·기술·경제 역량 진술을 삭제해도 논문 주장이 그대로면, 그 국가는 논의 대상이 아니다. 논의 수준·시점은 성립과 무관. 확신 없으면 낮은 쪽(불성립). 지정 JSON으로만 답하고 초록에 없는 정보 추측 금지.
```

## 2. 약식 결정트리 + 코드북 rubric + 경계 앵커 (배치 user 상단, 전문)

```
[약식 결정트리 — 각 항목에 다음 3단만 적용]
STEP1 referent(7항): 매칭 표현이 해당 국가(의 혁신)를 실제 가리키나? 비지시면 wrong_referent. 비지시 목록: 북한/디아스포라/대륙형용사(American=대륙)/대명사(소문자 us)/언어·질병명/통화·단위토큰(US$·KRW·¥·€)/국가명 포함 고유명(German Shepherd 등). 단 해당국 영토·관할(US Virgin Islands)은 wrong 아님(→dso). 과거·역사는 wrong 아님.
STEP2 역량진술(종착 술어 테스트): 종착 술어의 최종 귀속이 (i)혁신·기술 산출/역량 (ii)산업·기업 경쟁력 (iii)경제 성과·제도(혁신·기술·산업 연계분에 限) → in / (iv)서비스 전달·교육·복지·보건·행정 거버넌스·외교·순수 거시안정화(재정승수·통화정책·환율) → out. 연계 예외: 비역량 표현도 최종 귀속이 (i)~(iii)이면 in. false-friend: 계량모형 innovation(s)/innovation disturbance=VAR/SVAR 통계 충격·교란항 → 혁신 담론 아님. 역량진술 없으면: 국가 실체(기업·기관·지역·문서·시계열·응답자)가 수집·분석 대상=data_source_only(도메인 무관) / 장소·배경·소속·주최=passing_mention.
STEP3 역할(in인 경우): 주 대상=substantive / 비교준거 개별 귀속 완결명제=comparative_referent. 이름 나열·집합 선택 수식·얇은 1~2문장 벤치마크=passing_mention(out). 설계된 co-equal 비교=substantive.
[재정 요지] E: 순수 거시안정화 out. G: 정책수단 혁신(policy innovation)·규제 라벨=거버넌스(iv) out. F: 종착 술어는 in/out만 결정, out 후 범주는 역할로만('(iv)이므로 passing' 논법 금지). H: 국가명 포함 고유명 wrong. I: 다국 비교는 국가 수 아닌 설계(co-equal=substantive / 순위·나열 개별귀속=comparative). 매핑/순위 데이터(계량서지·특허·패널)에서 국가가 측정·순위 단위면 개별 수치 언급돼도 data_source_only. KR=대한민국(남한).
[경계 앵커 — dso 과판정 교정 (v2.1 재도입, 원 V앵커 14건 압축본 8건). 국가가 측정·표집·사례 단위면 혁신 수치가 있어도 dso]
· 미국 특허·계량서지로 기술역량 지표화(NFM SCI논문 분석) → data_source_only(국가=측정 단위).
· OECD 재생에너지 특허 패널에서 미국=혁신 1위(순위 산출) → data_source_only(순위=측정 결과).
· 미국·독일·한국·스웨덴 디지털경제 시가총액 측정·비교 → data_source_only(4개국=측정 단위).
· 미국 지역 모터스포츠 클러스터 형성 사례 → data_source_only(종착 주어=클러스터).
· 한국 R&D 보조금의 기업 추가성 패널 분석 → data_source_only(종착=기업, 한국=표집틀).
· 이탈리아 R&D 논문에서 미국=한 줄 벤치마크·실질 분석 없음 → passing_mention.
[경계 보존 in 앵커 — 국가 프레이밍/설계 비교는 여전히 in]
· 일본 편의점 발주시스템=일본식 경쟁무기(국가 특성 프레이밍) → substantive.
· 미국=brain circulation의 개별 귀속 비교준거(얇은 벤치마크 아님) → comparative_referent.
```

## 3. 배치 출력 형식 명세 (v2.0과 동일, 전문)

```
[출력 — 배치 JSON 배열만]
판정 대상 목록의 **모든** 항목에 대해 아래 스키마 객체를 원소로 갖는 JSON 배열 하나로만 답한다. 서술·코드펜스 금지.
각 원소 = {"dyad_id":"<입력 그대로 echo>","paper_id":"","country":"","category":"<substantive|comparative_referent|data_source_only|passing_mention|wrong_referent>","dyad_status":"<in|out>","role":"","confidence":<0~1>,"rationale":"<한 구절 태그>","referent_note":"<간단>"}
정합: in ⇔ category∈{substantive,comparative_referent}. **dyad_id는 반드시 입력값을 그대로 echo**(위치 아닌 dyad_id로 매칭). 목록의 모든 dyad_id를 빠짐없이 1회씩 포함.
```

## 4. 배치 user 조립 구조 (batch_assemble_v1.1.py — v1.0과 동일)

user = 약식 rubric+경계앵커(§2) + `[판정 대상 목록 (N건)]` + N개 항목 블록 + 출력 형식(§3). dyad_id echo 필수·위치 매칭 금지·고정 크기 50(canonical 오름차순)은 v2.0/§4-2와 동일.
