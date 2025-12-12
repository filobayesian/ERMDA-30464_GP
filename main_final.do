clear all
set more off, permanently

*============================*
*          SETUP             *
*============================*
global DATA ""           
global OUT  "output"          
cap mkdir "$OUT"

log close _all
cap log using "$OUT/analysis_final.log", replace text

*============================*
* PACKAGE INSTALLATION       *
*============================*
local packages ftools reghdfe estout coefplot parmest
foreach pkg of local packages {
    cap which `pkg'
    if _rc ssc install `pkg', replace
}

*============================*
*       LOAD DATA            *
*============================*
local regions molise basilicata
local first = 1
foreach r of local regions {
    if `first' {
        use "Data/non_derived/`r'.dta", clear
        local first = 0
    }
    else append using "Data/non_derived/`r'.dta"
}

*============================*
*  DATA CLEANING & SETUP     *
*============================*

keep id_worker year gender type wage contract_type sector_12cat region_res year_birth

destring region_res, replace

* For each worker, find their region (use mode in case of moves)
bysort id_worker: egen region_filled = mode(region_res), maxmode
replace region_res = region_filled if missing(region_res)
drop region_filled

*--- Treatment Variables ---*
gen byte treat_quake = (region_res == 12)
label var treat_quake "Molise resident"
label define trt 0 "Control" 1 "Molise"
label values treat_quake trt

*--- Wage Processing ---*
destring wage, replace force
label var wage "Annual wage (€)"

*--- Employment Indicator ---*
gen byte employed = (wage > 0 & !missing(wage)) | (type != 4 & !missing(type))
replace employed = . if missing(wage) & missing(type)
label var employed "Any employment"

*--- Cohort Filtering ---*
preserve
keep id_worker
duplicates drop
di "Cohort size: " _N
tempfile cohort_workers
save `cohort_workers'
restore

merge m:1 id_worker using `cohort_workers', keep(match) nogen
keep if inrange(year, 2000, 2004)

*--- Post-treatment indicator ---*
gen byte post_quake = (year >= 2003)
label var post_quake "Post 2003"

gen rel_year = year - 2002
label var rel_year "Year - 2002"

*--- Age calculation and age groups ---*
gen age = year - year_birth
label var age "Age in given year"

gen byte age_group = .
replace age_group = 1 if age <= 34 & !missing(age)
replace age_group = 2 if age >= 35 & age <= 55 & !missing(age)
replace age_group = 3 if age >= 56 & !missing(age)

label define age_grp 1 "≤34" 2 "35-55" 3 "≥56"
label values age_group age_grp
label var age_group "Age group"

*--- Employment Type Dummies ---*
gen byte y_private = (type == 1) if !missing(type)
gen byte y_public  = (type == 2) if !missing(type)
gen byte y_self    = (type == 3) if !missing(type)

label var y_private "Private employment (Pr)"
label var y_public  "Public employment (Pr)"
label var y_self    "Self-employment (Pr)"

*--- Log wage (with zeros for unemployed) ---*
gen double lnwage = ln(wage + 1) if wage > 0 & !missing(wage)
replace lnwage = 0 if employed == 0 | (missing(wage) & type == 4)
label var lnwage "Log(wage + 1)"

*============================*
*   SAMPLE DESCRIPTIVES      *
*   (for Report Section 3)   *
*============================*

*--- 1. Sample sizes by region ---*

// Worker-year observations by region
tab treat_quake, matcell(obs_by_region)
di "Basilicata worker-year obs: " obs_by_region[1,1]
di "Molise worker-year obs: " obs_by_region[2,1]

// Unique workers by region
preserve
bysort id_worker: keep if _n == 1
tab treat_quake, matcell(workers_by_region)
di "Basilicata unique workers: " workers_by_region[1,1]
di "Molise unique workers: " workers_by_region[2,1]
di "Total unique workers: " _N
restore

*--- 2. Pre-earthquake comparability (2000-2002) ---*
di _n "=== 2. PRE-EARTHQUAKE COMPARABILITY (2000-2002) ==="

// Define pre-period
gen byte pre_period = (year <= 2002)

// Age comparison
di _n "--- Age ---"
tabstat age if pre_period, by(treat_quake) stat(mean sd n) format(%9.2f)
ttest age if pre_period, by(treat_quake)

// Gender comparison (proportion female)
di _n "--- Gender (proportion female, assuming female=1) ---"
tabstat gender if pre_period, by(treat_quake) stat(mean sd n) format(%9.3f)
ttest gender if pre_period, by(treat_quake)

// Employment rate comparison
di _n "--- Employment Rate ---"
tabstat employed if pre_period, by(treat_quake) stat(mean sd n) format(%9.3f)
ttest employed if pre_period, by(treat_quake)

// Wages among employed
di _n "--- Wages (conditional on employment) ---"
tabstat wage if pre_period & employed == 1, by(treat_quake) stat(mean sd n) format(%9.2f)
ttest wage if pre_period & employed == 1, by(treat_quake)

*--- 3. Employment rates by age group ---*
di _n "=== 3. EMPLOYMENT RATES BY AGE GROUP ==="

// Overall by age group
di _n "--- Overall employment rates by age group ---"
tabstat employed if pre_period, by(age_group) stat(mean n) format(%9.3f)

// By age group AND region
di _n "--- Employment rates by age group and region ---"
table age_group treat_quake if pre_period, stat(mean employed) stat(n employed) nformat(%9.3f)

// Specific values for report
di _n "--- Specific values for report ---"
forvalues a = 1/3 {
    forvalues t = 0/1 {
        qui sum employed if pre_period & age_group == `a' & treat_quake == `t'
        local region = cond(`t' == 0, "Basilicata", "Molise")
        local agelab: label age_grp `a'
        di "`region', Age `agelab': " %5.1f r(mean)*100 "%"
    }
}

*--- 4. Baseline rates for percentage calculations ---*
di _n "=== 4. BASELINE RATES (for percentage decline calculations) ==="

// Molise pre-earthquake employment rate
qui sum employed if pre_period & treat_quake == 1
di "Molise pre-earthquake employment rate: " %5.3f r(mean) " (" %5.1f r(mean)*100 "%)"
local molise_emp_rate = r(mean)

// Mid-career (35-55) baseline employment rate
qui sum employed if pre_period & age_group == 2
di "Mid-career (35-55) baseline employment rate: " %5.3f r(mean) " (" %5.1f r(mean)*100 "%)"

// Private sector baseline rate
qui sum y_private if pre_period & treat_quake == 1
di "Molise baseline private employment rate: " %5.3f r(mean) " (" %5.1f r(mean)*100 "%)"
local molise_private_rate = r(mean)

*--- 5. Percentage decline calculations ---*
di _n "=== 5. PERCENTAGE DECLINE CALCULATIONS ==="

// Employment decline as % of baseline
local emp_coef = 0.0093
di "Employment decline (-0.0093) as % of Molise baseline (" %5.1f `molise_emp_rate'*100 "%): " %5.1f (`emp_coef'/`molise_emp_rate')*100 "%"

// Mid-career decline as % of baseline
local midcareer_coef = 0.0181
qui sum employed if pre_period & age_group == 2 & treat_quake == 1
local midcareer_baseline = r(mean)
di "Mid-career decline (-0.0181) as % of baseline (" %5.1f `midcareer_baseline'*100 "%): " %5.1f (`midcareer_coef'/`midcareer_baseline')*100 "%"

// Private sector decline as % of baseline
local private_coef = 0.0128
di "Private decline (-0.0128) as % of Molise baseline (" %5.1f `molise_private_rate'*100 "%): " %5.1f (`private_coef'/`molise_private_rate')*100 "%"

*--- 6. Job loss calculation ---*
// Number of unique Molise workers
preserve
keep if treat_quake == 1
bysort id_worker: keep if _n == 1
local molise_workers = _N
di "Unique Molise workers: " `molise_workers'
restore

// Estimated private jobs lost
local jobs_lost = `molise_workers' * 0.0128
di "Estimated private jobs lost: " %5.0f `jobs_lost' " (= " `molise_workers' " × 0.0128)"
*--- 7. Public offset calculation ---*
di _n "=== 7. PUBLIC OFFSET CALCULATION ==="

local private_loss = 0.0128
local public_gain = 0.0022
local offset_pct = (`public_gain' / `private_loss') * 100
di "Public offset as % of private loss: " %5.1f `offset_pct' "%"
di "(0.0022 / 0.0128 = " %5.3f `public_gain'/`private_loss' ")"

drop pre_period

*============================*
* MAIN REGRESSIONS        *
*============================*
local absorb_spec absorb(year region_res) vce(cluster id_worker)

*--- (A) Main DiD: Employment, Log Earnings (Uncond.), Log Wage (Cond.) ---*

// A1: Employment (Table 1, Col 1) -> Extensive Margin
eststo A_employed: reghdfe employed i.post_quake##i.treat_quake, `absorb_spec'

// A2: Unconditional Log Earnings (Table 1, Col 2) -> Total Welfare Effect
eststo A_lnwage_uncond: reghdfe lnwage i.post_quake##i.treat_quake, `absorb_spec'

// A3: Conditional Log Wage (Table 1, Col 3) -> Price Effect (Intensive Margin)
eststo A_lnwage_cond: reghdfe lnwage i.post_quake##i.treat_quake if employed == 1, `absorb_spec'

*--- (B) Employment Type DiD (Figure 2, Panel B) ---*
foreach y in y_private y_public y_self {
    eststo B_`y': reghdfe `y' i.treat_quake##i.post_quake, `absorb_spec'
}


*--- (F) Age Heterogeneity (Table 1, Cols 4-6; Figure 2, Panel F) ---*
forvalues a = 1/3 {
    eststo F_age`a': reghdfe employed i.treat_quake##i.post_quake if age_group == `a', `absorb_spec'
}


*============================*
*   EVENT STUDY (Figure 3)   *
*============================*

preserve
keep if inrange(rel_year, -2, 2)

cap drop event_*
forval k = -2/2 {
    if `k' != 0 {
        local suffix = cond(`k' < 0, "m" + string(abs(`k')), string(`k'))
        gen byte event_`suffix' = (rel_year == `k' & treat_quake == 1)
    }
}

eststo C_employed: reghdfe employed event_*, `absorb_spec'

coefplot C_employed, keep(event_*) vertical yline(0, lp(dash)) ///
    ciopts(recast(rcap)) title("Event study: employed") ///
    ytitle("Effect vs rel_year=0") xtitle("Relative year") ///
    order(event_m2 event_m1 event_1 event_2)
graph export "$OUT/eventstudy_employed.png", replace

restore


*============================*
*   ROBUSTNESS CHECKS        *
*============================*

// (R1) Different treatment timing (use 2002 vs 2003)
gen byte post_quake_2002 = (year >= 2002)
eststo R1: reghdfe employed i.post_quake_2002##i.treat_quake, `absorb_spec'
drop post_quake_2002

// (R2) Exclude transition year (drop 2002)
eststo R2: reghdfe employed i.post_quake##i.treat_quake if year != 2002, `absorb_spec'

// (R3) Balanced panel only
bys id_worker: gen n_obs = _N
eststo R3: reghdfe employed i.post_quake##i.treat_quake if n_obs == 5, `absorb_spec'
drop n_obs


*============================*
*      PLACEBO TESTS         *
*============================*

// (P1) Placebo treatment year (pretend shock was in 2001)
gen byte fake_post = (year >= 2001)
eststo P1: reghdfe employed i.fake_post##i.treat_quake if year <= 2002, `absorb_spec'
drop fake_post

// (P2) Placebo outcome (gender - shouldn't change)
destring gender, replace force
eststo P2: reghdfe gender i.post_quake##i.treat_quake, `absorb_spec'

// (P3) Randomization test: assign treatment to random workers
set seed 12345
gen random_treat = runiform() > 0.5
eststo P3: reghdfe employed i.post_quake##i.random_treat, `absorb_spec'
drop random_treat


*============================*
*         FIGURES            *
*============================*

// Figure 2, Panel F: Age heterogeneity
coefplot ///
    (F_age1, keep(1.treat_quake#1.post_quake) label("≤34")) ///
    (F_age2, keep(1.treat_quake#1.post_quake) label("35-55")) ///
    (F_age3, keep(1.treat_quake#1.post_quake) label("≥56")), ///
    vertical yline(0, lp(dash)) ciopts(recast(rcap)) ///
    coeflabels(1.treat_quake#1.post_quake = "Treat×Post") ///
    title("F — DiD within age groups") ytitle("Coefficient") xtitle("")
graph export "$OUT/plot_F_age.png", replace

// Figure 2, Panel B: Employment type
coefplot ///
    (B_y_private, keep(1.treat_quake#1.post_quake) label("Private")) ///
    (B_y_public,  keep(1.treat_quake#1.post_quake) label("Public")) ///
    (B_y_self,    keep(1.treat_quake#1.post_quake) label("Self")), ///
    vertical yline(0, lp(dash)) ciopts(recast(rcap)) ///
    coeflabels(1.treat_quake#1.post_quake = "Treat×Post") ///
    title("B — Type-specific DiD") ytitle("Coefficient") xtitle("")
graph export "$OUT/plot_B_types.png", replace


*============================*
* EXPORT RESULTS        *
*============================*
local star_spec star(* 0.10 ** 0.05 *** 0.01)
local table_opts replace se r2 ar2 label nonotes b(%9.4f) se(%9.4f) `star_spec'

// Table 1: Main Results
// Note: We use A_lnwage_uncond (Col 2) and A_lnwage_cond (Col 3)
esttab A_employed A_lnwage_uncond A_lnwage_cond F_age1 F_age2 F_age3 using "$OUT/table1_main_results.txt", ///
    `table_opts' ///
    mtitles("Employment" "Log Earn (Uncond)" "Log Wage (Cond)" "Age ≤34" "Age 35-55" "Age ≥56") ///
    title("Table 1: Main Results")

// Robustness checks
esttab R1 R2 R3 using "$OUT/robustness_checks.txt", ///
    `table_opts' ///
    mtitles("Alt. Timing" "Excl. 2002" "Balanced Panel") ///
    title("Robustness Checks")

// Placebo tests
esttab P1 P2 P3 using "$OUT/placebo_tests.txt", ///
    `table_opts' ///
    mtitles("Fake 2001" "Gender" "Random Treat") ///
    title("Placebo Tests")

// Employment type (for reference)
esttab B_y_private B_y_public B_y_self using "$OUT/employment_type.txt", ///
    `table_opts' ///
    mtitles("Private" "Public" "Self") ///
    title("Employment Type Decomposition")

log close _all
