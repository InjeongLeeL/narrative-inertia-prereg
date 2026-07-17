#!/usr/bin/env python3
# batch_assemble_v1.1.py — 설계 E 사전등록 수정안 v3.13 §3 동결 산출물 (v1.0 + dso 경계 앵커 재도입).
# 역할: 대리라벨 **배치 조립 계층**. 입력=population_main_v1.csv(동결본, cdf94841…) 또는 그 청크,
#   출력=배치별 {batch_id, dyad_ids, system, user}. 측정 정의는 코드북 v1.4 준거(SYSTEM 프롬프트 = v1.6 바이트 동일).
#   V 유래 앵커: **일부 승계** — dso 경계 반례/경계 앵커 8건(원 14건 내 압축 조달)만 재도입. 상세·pilot_id 매핑 공시 = prompt_template_v2.1_batch.md.
# 배치 규칙(v3.12 §4-2): 청크 내 dyad_id canonical 오름차순·고정 크기 50(마지막 잔여 <50), dyad_id echo 필수, 위치매칭 금지.
# 사용: python batch_assemble_v1.1.py --chunk out/arm_E/chunks/chunk01.csv --out out/arm_E/batches/chunk01_batches.jsonl --map out/arm_E/batches/chunk01_map.csv
import csv, json, os, sys, argparse
csv.field_size_limit(10**8)
BASE=os.path.dirname(os.path.abspath(__file__))
def P(*a): return os.path.join(BASE,*a)
BATCH_SIZE=50

COUNTRY_FULL={'DE':'독일(Germany)','JP':'일본(Japan)','KR':'대한민국(남한)','US':'미국(United States)'}
FLAG_HINT={'flag_north_korea':"북한(NK/DPRK/Pyongyang) 동반 — 'Korea'가 북한 지칭인지 확인.",
 'flag_diaspora':"'Korean/Japanese/German American' 디아스포라 — 남한 혁신 vs 미국 내 집단 구분.",
 'flag_us_continental_only':"'American'이 모두 대륙 형용사일 수 있음 — 미국(USA) 대상인지 확인.",
 'flag_us_bare_token':"대문자 'US'로만 탐지 — 국가 미국 vs 대명사/통화기호(US$) 확인."}

# ---- SYSTEM 프롬프트: v1.6 바이트 동일(코드북 핵심·V 비유래) ----
SYSTEM=("당신은 혁신정책·과학기술학 서지 스크리닝 전문가다. 논문 초록에서 '특정 국가의 혁신(시스템·정책·활동·성과)이 실제 논의 대상인지' 판정한다. "
 "지배 규칙(삭제 테스트): 그 국가의 혁신·기술·경제 역량 진술을 삭제해도 논문 주장이 그대로면, 그 국가는 논의 대상이 아니다. "
 "논의 수준·시점은 성립과 무관. 확신 없으면 낮은 쪽(불성립). 지정 JSON으로만 답하고 초록에 없는 정보 추측 금지.")

# ---- 약식 결정트리 + 코드북 rubric(v1.4 준거) + dso 경계 앵커(일부 승계, 원 14건 압축본 8건) ----
BATCH_RULES=("[약식 결정트리 — 각 항목에 다음 3단만 적용]\n"
 "STEP1 referent(7항): 매칭 표현이 해당 국가(의 혁신)를 실제 가리키나? 비지시면 wrong_referent. "
 "비지시 목록: 북한/디아스포라/대륙형용사(American=대륙)/대명사(소문자 us)/언어·질병명/통화·단위토큰(US$·KRW·¥·€)/국가명 포함 고유명(German Shepherd 등). "
 "단 해당국 영토·관할(US Virgin Islands)은 wrong 아님(→dso). 과거·역사는 wrong 아님.\n"
 "STEP2 역량진술(종착 술어 테스트): 종착 술어의 최종 귀속이 (i)혁신·기술 산출/역량 (ii)산업·기업 경쟁력 (iii)경제 성과·제도(혁신·기술·산업 연계분에 限) → in / "
 "(iv)서비스 전달·교육·복지·보건·행정 거버넌스·외교·순수 거시안정화(재정승수·통화정책·환율) → out. 연계 예외: 비역량 표현도 최종 귀속이 (i)~(iii)이면 in. "
 "false-friend: 계량모형 innovation(s)/innovation disturbance=VAR/SVAR 통계 충격·교란항 → 혁신 담론 아님. "
 "역량진술 없으면: 국가 실체(기업·기관·지역·문서·시계열·응답자)가 수집·분석 대상=data_source_only(도메인 무관) / 장소·배경·소속·주최=passing_mention.\n"
 "STEP3 역할(in인 경우): 주 대상=substantive / 비교준거 개별 귀속 완결명제=comparative_referent. "
 "이름 나열·집합 선택 수식·얇은 1~2문장 벤치마크=passing_mention(out). 설계된 co-equal 비교=substantive.\n"
 "[재정 요지] E: 순수 거시안정화 out. G: 정책수단 혁신(policy innovation)·규제 라벨=거버넌스(iv) out. "
 "F: 종착 술어는 in/out만 결정, out 후 범주는 역할로만('(iv)이므로 passing' 논법 금지). "
 "H: 국가명 포함 고유명 wrong. I: 다국 비교는 국가 수 아닌 설계(co-equal=substantive / 순위·나열 개별귀속=comparative). "
 "매핑/순위 데이터(계량서지·특허·패널)에서 국가가 측정·순위 단위면 개별 수치 언급돼도 data_source_only. KR=대한민국(남한).\n"
        "[경계 앵커 — dso 과판정 교정 (v2.1 재도입, 원 V앵커 14건 압축본 8건). 국가가 측정·표집·사례 단위면 혁신 수치가 있어도 dso]\n"
        "· 미국 특허·계량서지로 기술역량 지표화(NFM SCI논문 분석) → data_source_only(국가=측정 단위).\n"
        "· OECD 재생에너지 특허 패널에서 미국=혁신 1위(순위 산출) → data_source_only(순위=측정 결과).\n"
        "· 미국·독일·한국·스웨덴 디지털경제 시가총액 측정·비교 → data_source_only(4개국=측정 단위).\n"
        "· 미국 지역 모터스포츠 클러스터 형성 사례 → data_source_only(종착 주어=클러스터).\n"
        "· 한국 R&D 보조금의 기업 추가성 패널 분석 → data_source_only(종착=기업, 한국=표집틀).\n"
        "· 이탈리아 R&D 논문에서 미국=한 줄 벤치마크·실질 분석 없음 → passing_mention.\n"
        "[경계 보존 in 앵커 — 국가 프레이밍/설계 비교는 여전히 in]\n"
        "· 일본 편의점 발주시스템=일본식 경쟁무기(국가 특성 프레이밍) → substantive.\n"
        "· 미국=brain circulation의 개별 귀속 비교준거(얇은 벤치마크 아님) → comparative_referent.")

OUTPUT_SPEC=("[출력 — 배치 JSON 배열만]\n"
 "판정 대상 목록의 **모든** 항목에 대해 아래 스키마 객체를 원소로 갖는 JSON 배열 하나로만 답한다. 서술·코드펜스 금지.\n"
 '각 원소 = {"dyad_id":"<입력 그대로 echo>","paper_id":"","country":"","category":"<substantive|comparative_referent|data_source_only|passing_mention|wrong_referent>",'
 '"dyad_status":"<in|out>","role":"","confidence":<0~1>,"rationale":"<한 구절 태그>","referent_note":"<간단>"}\n'
 "정합: in ⇔ category∈{substantive,comparative_referent}. **dyad_id는 반드시 입력값을 그대로 echo**(위치 아닌 dyad_id로 매칭). 목록의 모든 dyad_id를 빠짐없이 1회씩 포함.")

def render_item(i, x):
    cf=COUNTRY_FULL[x['country']]
    if x['country']=='KR' and x.get('flag_kr_dyad_only')=='1': cf+=" (referent: 남한 한정)"
    hints=[FLAG_HINT[k] for k in FLAG_HINT if x.get(k)=='1']; hint=" ".join(hints) if hints else "특이 플래그 없음."
    notice="※근거 제한(초록<100단어) — 명백할 때만 성립." if x['wc']<100 else ""
    return (f"[{i}] dyad_id={x['dyad_id']} | 판정대상국={cf}\n"
            f"제목:{x['title']} | 저널:{x['journal']} | 연도:{x['year']} | 키워드:{x['keywords']}\n"
            f"초록:{x['abstract']}\n{notice}<flags>{hint}</flags>")

def build_user(items):
    body="\n\n".join(render_item(i+1, x) for i,x in enumerate(items))
    return (BATCH_RULES+"\n\n"+f"[판정 대상 목록 ({len(items)}건) — 각 항목 독립 판정]\n\n"+body+"\n\n"+OUTPUT_SPEC)

def load_join():
    corp={}
    with open(P('corpus_v1.0.csv'),encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            corp[r['paper_id']]={'Title':r.get('Title','')or'','Abstract':(r.get('Abstract','')or'').strip(),
                                 'Keywords':r.get('Keywords','')or'','Journal':r.get('Journal','')or'','Year':r.get('Year','')or''}
    cand={}
    with open(P('dyad_candidates_v1.0.csv'),encoding='utf-8-sig') as f:
        for r in csv.DictReader(f): cand[(r['paper_id'],r['country'])]=r
    return corp,cand

def assemble(chunk_csv, out_path, map_path):
    corp,cand=load_join()
    rows=list(csv.DictReader(open(chunk_csv,encoding='utf-8-sig')))
    rows.sort(key=lambda r:r['dyad_id'])                       # canonical 오름차순
    items=[]
    for r in rows:
        c=corp.get(r['paper_id'],{}); src=cand.get((r['paper_id'],r['country']),{})
        ab=c.get('Abstract',''); wc=0 if (not ab or ab.lower()=='nan') else len(ab.split())
        it={'dyad_id':r['dyad_id'],'paper_id':r['paper_id'],'country':r['country'],
            'title':c.get('Title',''),'journal':c.get('Journal',''),'year':c.get('Year',''),
            'keywords':c.get('Keywords',''),'abstract':ab,'wc':wc}
        for k in ('flag_north_korea','flag_diaspora','flag_us_continental_only','flag_us_bare_token','flag_kr_dyad_only'):
            it[k]=src.get(k,'')
        items.append(it)
    cid=os.path.splitext(os.path.basename(chunk_csv))[0]
    nb=0; mapping=[]
    os.makedirs(os.path.dirname(out_path),exist_ok=True)
    with open(out_path,'w',encoding='utf-8') as out:
        for b in range(0,len(items),BATCH_SIZE):
            seg=items[b:b+BATCH_SIZE]; bid=f"{cid}_b{b//BATCH_SIZE+1:02d}"
            rec={'batch_id':bid,'dyad_ids':[x['dyad_id'] for x in seg],'system':SYSTEM,'user':build_user(seg)}
            out.write(json.dumps(rec,ensure_ascii=False)+'\n'); nb+=1
            for x in seg: mapping.append((bid,x['dyad_id']))
    if map_path:
        with open(map_path,'w',encoding='utf-8',newline='') as f:
            w=csv.writer(f); w.writerow(['batch_id','dyad_id']); w.writerows(mapping)
    print(f"[batch_assemble] {chunk_csv}: {len(items)}건 → {nb}배치(크기{BATCH_SIZE}) → {out_path}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--chunk',required=True); ap.add_argument('--out',required=True); ap.add_argument('--map',default=None)
    a=ap.parse_args(); assemble(a.chunk,a.out,a.map)

if __name__=='__main__': main()
