# screen_dsl_run_E1.R — 설계 E DSL 주 추정 (동결 screen_analysis_spec_v1.md §1·§2 이행, 완성본)
# ★Cowork 샌드박스 R 미설치 → IJ가 R 4.x + dsl v0.1.0 환경에서 실행. 콘솔 전체 로그(sessionInfo·fold 불변식) 저장.
# 완성(결과 前, spec §2 명시 허용 wrapper): (1) paper-fold 격리 불변식 실코드 (2) 민감도 2종(dyad SE·W 제외) (3) assert.
#   커밋 전 보강: (a) 전 24,149 country_period NA assert (b) wrapper fold m0/m1 결측 가드.
# 입력 해시 대조 권장: gold_E_v1.csv 4cc785f4… / surrogate_labels_v1.csv 49b06ace… / gold_prob_ledger_v1.csv f615bc76…
#   / population_main_v1.csv cdf94841… / wave1_alloc_result_v1.csv e0090384… / dyad_candidates_v1.0.csv c4853ec8…(Year 3열)

suppressPackageStartupMessages(library(dsl))
stopifnot(as.character(packageVersion("dsl")) == "0.1.0")
set.seed(20260720)

## ---------- 데이터 조립 ----------
rd  <- function(f) read.csv(f, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
g   <- rd("gold_E_v1.csv"); sur <- rd("surrogate_labels_v1.csv"); led <- rd("gold_prob_ledger_v1.csv")
pop <- rd("population_main_v1.csv"); cand <- rd("dyad_candidates_v1.0.csv")

## assert 1 — 연도 NA 조용한 기본처리 금지·중단
cand$key <- paste(cand$paper_id, cand$country, sep = "_")
yr_int <- suppressWarnings(as.integer(cand$Year))
stopifnot("연도 파싱 실패(NA) 존재 — 중단" = !any(is.na(yr_int)))
period <- function(y) ifelse(y <= 2008, "2000-2008", ifelse(y <= 2017, "2009-2017", "2018-2025"))
cp_by_key <- setNames(paste(cand$country, period(yr_int), sep = "|"), cand$key)
pi_num <- function(s) vapply(s, function(x) if (grepl("/", x)) eval(parse(text = x)) else as.numeric(x), numeric(1))

base <- data.frame(dyad_id = pop$dyad_id, paper_id = pop$paper_id, country = pop$country, stringsAsFactors = FALSE)
base$country_period <- cp_by_key[base$dyad_id]
base$surrogate_analysis_status_bin <- as.integer(sur$surrogate_analysis_status[match(base$dyad_id, sur$dyad_id)] == "in")
base$pi_final    <- pi_num(led$pi_final[match(base$dyad_id, led$dyad_id)])
base$screen_gold <- g$screen_gold[match(base$dyad_id, g$dyad_id)]
base$labeled     <- as.integer(!is.na(base$screen_gold))
stopifnot(sum(base$labeled) == 1475)
## 보강(a): 전 24,149행 country_period NA 없음
stopifnot("country_period NA 존재(전 24,149 커버) — 중단" = !any(is.na(base$country_period)))

## assert 2 — 1,475 gold country_period ↔ 원장 하위층 정합
lab_idx <- which(base$labeled == 1)
sub_stratum <- sub("\\|(in|out)$", "", led$substratum[match(base$dyad_id[lab_idx], led$dyad_id)])
cp_geo <- sub("\\|(off|on)$", "", sub_stratum)
stopifnot("country_period ↔ 원장 하위층 정합 위반" = all(cp_geo == base$country_period[lab_idx]))
cat("[assert] 연도 NA 0 · country_period NA 0(24,149) · 원장 하위층 정합 1,475 통과\n")

## ---------- (spec §1) DSL 주 추정 — 일자일획 변경 금지 ----------
fit_main <- dsl(model = "lm", formula = screen_gold ~ as.factor(country_period) - 1,
                predicted_var = "screen_gold", prediction = "surrogate_analysis_status_bin",
                sample_prob = "pi_final", cluster = "paper_id",
                cross_fit = 5, sample_split = 5, seed = 20260720, data = base)
cat("\n===== DSL 주추정 (cluster=paper_id) =====\n"); print(summary(fit_main))

## 민감도 A — dyad 독립 SE (cluster 제거)
fit_dyad <- dsl(model = "lm", formula = screen_gold ~ as.factor(country_period) - 1,
                predicted_var = "screen_gold", prediction = "surrogate_analysis_status_bin",
                sample_prob = "pi_final", cluster = NULL,
                cross_fit = 5, sample_split = 5, seed = 20260720, data = base)
cat("\n===== 민감도 A: dyad 독립 SE =====\n"); print(summary(fit_dyad))

## 민감도 B — W 제외(wave 1,200만)
Wids <- g$dyad_id[g$certainty == 1]
base_wo <- base
base_wo$screen_gold[base_wo$dyad_id %in% Wids] <- NA
base_wo$labeled <- as.integer(!is.na(base_wo$screen_gold))
stopifnot(sum(base_wo$labeled) == 1200)
fit_wo <- dsl(model = "lm", formula = screen_gold ~ as.factor(country_period) - 1,
              predicted_var = "screen_gold", prediction = "surrogate_analysis_status_bin",
              sample_prob = "pi_final", cluster = "paper_id",
              cross_fit = 5, sample_split = 5, seed = 20260720, data = base_wo)
cat("\n===== 민감도 B: W 제외(wave 1,200만) =====\n"); print(summary(fit_wo))

## ---------- (spec §2) paper-fold 격리 불변식 + group-fold 교차적합 wrapper ----------
K <- 5; SPLITS <- 5
cps <- sort(unique(base$country_period))
group_fold_dsl <- function(dat, cluster_paper = TRUE) {
  papers <- unique(dat$paper_id)
  thetas <- matrix(NA, SPLITS, length(cps), dimnames = list(NULL, cps))
  psi_store <- vector("list", SPLITS); iso_log <- character(0)
  for (s in seq_len(SPLITS)) {
    set.seed(20260720 + s)
    fold_of_paper <- setNames(sample(rep(seq_len(K), length.out = length(papers))), papers)
    fold <- fold_of_paper[dat$paper_id]
    fhat <- rep(NA_real_, nrow(dat))
    for (k in seq_len(K)) {
      test <- which(fold == k); train <- which(fold != k)
      tp <- unique(dat$paper_id[test]); rp <- unique(dat$paper_id[train])
      viol <- length(intersect(tp, rp))
      iso_log <- c(iso_log, sprintf("split %d fold %d: train∩test paper = %d", s, k, viol))
      stopifnot("★paper-fold 격리 불변식 위반 — 중단" = viol == 0)
      tr_lab <- train[dat$labeled[train] == 1]
      ## 보강(b): fold train에 대리 in/out 한쪽 부재 시 중단(NaN 전파 방지)
      stopifnot("fold train labeled에 대리 in/out 한쪽 부재 — 중단" =
                any(dat$surrogate_analysis_status_bin[tr_lab] == 1) && any(dat$surrogate_analysis_status_bin[tr_lab] == 0))
      m1 <- mean(dat$screen_gold[tr_lab][dat$surrogate_analysis_status_bin[tr_lab] == 1])
      m0 <- mean(dat$screen_gold[tr_lab][dat$surrogate_analysis_status_bin[tr_lab] == 0])
      fhat[test] <- ifelse(dat$surrogate_analysis_status_bin[test] == 1, m1, m0)
    }
    R <- dat$labeled; Y <- ifelse(is.na(dat$screen_gold), 0, dat$screen_gold)
    ytil <- fhat + (R / dat$pi_final) * (Y - fhat)
    psi <- matrix(0, nrow(dat), length(cps), dimnames = list(NULL, cps))
    for (j in seq_along(cps)) {
      inc <- dat$country_period == cps[j]; Nc <- sum(inc)
      thetas[s, j] <- mean(ytil[inc]); psi[inc, j] <- (ytil[inc] - thetas[s, j]) / Nc
    }
    psi_store[[s]] <- list(psi = psi)
  }
  theta <- colMeans(thetas); se <- numeric(length(cps)); names(se) <- cps
  for (j in seq_along(cps)) {
    psi_avg <- rowMeans(sapply(psi_store, function(z) z$psi[, j]))
    if (cluster_paper) { agg <- tapply(psi_avg, dat$paper_id, sum); se[j] <- sqrt(sum(agg^2)) }
    else { se[j] <- sqrt(sum(psi_avg^2)) }
  }
  list(theta = theta, se = se, iso_log = iso_log)
}
cat("\n===== (spec §2) group-fold 격리 wrapper — DSL 재현 + 불변식 =====\n")
wrap_main <- group_fold_dsl(base, cluster_paper = TRUE)
wrap_dyad <- group_fold_dsl(base, cluster_paper = FALSE)
wrap_wo   <- group_fold_dsl(base_wo, cluster_paper = TRUE)
cat(paste(wrap_main$iso_log, collapse = "\n"), "\n")
cat("불변식: 전 ", SPLITS * K, " 반복 train∩test paper = 0 (위반 시 stopifnot 중단)\n", sep = "")

## ---------- 출력: 12셀 표 + SE 절감 ----------
go <- rd("gold_only_estimates_v1.csv")
out <- data.frame(country_period = cps,
                  dsl_p = round(wrap_main$theta, 4), dsl_se = round(wrap_main$se, 4),
                  dsl_ci_lo = round(wrap_main$theta - 1.959964 * wrap_main$se, 4),
                  dsl_ci_hi = round(wrap_main$theta + 1.959964 * wrap_main$se, 4),
                  dsl_dyadSE = round(wrap_dyad$se, 4), dsl_Wexcl_p = round(wrap_wo$theta, 4),
                  gold_only_p = go$p_hat[match(cps, go$country_period)],
                  gold_only_se = go$SE[match(cps, go$country_period)])
out$SE_reduction_vs_goldonly <- round(1 - out$dsl_se / out$gold_only_se, 3)
cat("\n===== 12셀 결과 (DSL wrapper vs gold-only) =====\n"); print(out, row.names = FALSE)
write.csv(out, "screen_dsl_results_E1.csv", row.names = FALSE)
cat("\n※ package dsl() summary(fit_main) vs wrapper theta 정합(≈) IJ 대조. 불일치 시 원인 보고(중단).\n")
cat("\n===== sessionInfo =====\n"); print(sessionInfo())
