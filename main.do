clear all
set more off, permanently
*============================*
*          PATHS             *
*============================*
global DATA ""           
global OUT  ""          
cap mkdir "$OUT"

log close _all
cap log using "$OUT/DiD_DDD_dynamic.log", replace text
*============================*
* PACKAGE CHECKS (Robust) *
*============================*
* 1. Uninstall both packages to ensure a clean state
*cap ado uninstall reghdfe
*cap ado uninstall ftools

* 2. Clear Stata's ado-file cache (crucial step)
*discard

* 3. Re-install in the correct order: ftools THEN reghdfe
cap which ftools
if _rc ssc install ftools, replace
cap which reghdfe
if _rc ssc install reghdfe, replace

* 4. Install other packages
cap which estout
if _rc ssc install estout, replace
cap which coefplot
if _rc ssc install coefplot, replace
cap which parmest
if _rc ssc install parmest, replace
*============================*
*       LOAD THE DATA        *
*============================*
* Use the FILTERED datasets directly (as requested).
* >>> EDIT these filenames if your names/paths differ <<<
local M_file "Data/derived/molise_filtered.dta" 
local B_file "Data/derived/basilicata_filtered.dta"
*local P_file "derived/puglia_filtered.dta"

use `M_file', clear
append using `B_file'
*append using `P_file'
*============================*
*   TREATMENT DEFINITIONS    *
*============================*
destring region_res, replace
* Molise treated, post from 2003 (quake 31 Oct 2002)
cap drop treat_quake post_quake
gen byte treat_quake = region_res==12
label var treat_quake "Molise resident"
local quake_cutoff = 2003
gen byte post_quake  = year >= `quake_cutoff'
label var post_quake  "Post 2003"

* Relative year for dynamic DiD (C)
cap drop rel_year
gen rel_year = year - 2002    // event year = 2002
label var rel_year "Year - 2002"
*============================*
*         OUTCOMES           *
*============================*
* The spec calls for employment + earnings. We run: employed, wage (level), lnwage (log).
cap drop lnwage
gen double lnwage = ln(wage + 1)

local outcomes employed wage lnwage
eststo clear
*====================================================*
*   (A) Region-based DiD: Molise vs Basilicata+Puglia
*====================================================*
foreach y of local outcomes {
    quietly count if !missing(`y')
    if r(N)>0 {
		eststo A_`y': reghdfe `y' c.post_quake##i.treat_quake, ///
			absorb(i.year i.region_res) vce(cluster id_worker)
        estadd local model "A: Region DiD", replace
        estadd local depvar "`y'", replace
    }
}
*=======================================*
* (B) DDD: By Employment Type (Base=Non-employed)
*=======================================*
foreach y of local outcomes {
    quietly count if !missing(`y')
    if r(N)>0 {
        * Use ib4.type to set 'Non-employed' (value 4) as the reference category
		eststo B_`y': reghdfe `y' c.post_quake##i.treat_quake##ib1.type, ///
			absorb(i.year i.region_res) vce(cluster id_worker)
        estadd local model "B: DDD (Type x Quake, Base=4)", replace
        estadd local depvar "`y'", replace
    }
}
*==================================*
* (C) Dynamic DiD (Event-Study)
* WORKAROUND: Manual Dummies
*==================================*
keep if inrange(rel_year, -5, 5)

* 1. Create manual event-study dummies
* This bypasses the reghdfe parser bug
local es_dummies ""
forval k = -5/5 {
    if `k' != -1 { // Skip base year -1
        * Create clean varname (e.g., event_m5, event_0, event_5)
        local suffix = subinstr("`k'", "-", "m", 1)
        
        * Gen the dummy: (rel_year == k) AND (treated)
        gen byte event_`suffix' = (rel_year == `k' & treat_quake == 1)
        
        * Add new dummy to the regression varlist
        local es_dummies `es_dummies' event_`suffix'
    }
}

* 2. Redefine _evtstore program to accept a filepath
cap program drop _evtstore
program define _evtstore, rclass
    syntax varname [if] [in], Filepath(string) // <-- ADDED: Accepts filepath option
    
    tempname b V
    mat `b' = e(b)
    mat `V' = e(V)
    
    * This command replaces data in memory AND clears globals
    parmest, norestore
    
    * Keep only coefficients for our manual dummies (event_m5, etc.)
    keep if strpos(parm, "event_") == 1
    
    * Extract the integer rel_year from the parm label
    gen str10 rel_str = subinstr(parm, "event_", "", 1)
    replace rel_str = subinstr(rel_str, "m", "-", 1)
    gen rel = real(rel_str)

    rename estimate beta
    rename min95 ci_lo
    rename max95 ci_hi
    keep rel beta ci_lo ci_hi
    sort rel
    
    * Export the CSV from *inside* the program using the passed path
    export delimited using "`filepath'", replace // <-- CHANGED

    tempfile es
    save `es', replace
    return local esfile `es'
end

* 3. Run regression loop using manual dummies
foreach y of local outcomes {
    quietly count if !missing(`y')
    if r(N)>0 {
        
        preserve 

        * Event-study regression
        eststo C_`y': reghdfe `y' `es_dummies', ///
            absorb(i.year i.region_res) vce(cluster id_worker)
        estadd local model "C: Dynamic DiD", replace
        estadd local depvar "`y'", replace

        * --- ROBUST PATH FIX ---
        * Re-define global path. This makes the loop runnable 
        * on its own and protects against parmest clearing globals.
        global OUT "./Data"
        cap mkdir "$OUT"
        
        * Define output paths *before* parmest is called
        local csv_outfile = "$OUT/eventstudy_`y'.csv"
        local png_outfile = "$OUT/eventstudy_`y'.png"
        * --- END FIX ---
        
        * Call the program, passing the pre-defined CSV path
        * This will run parmest and export the CSV
        quietly _evtstore `y', filepath("`csv_outfile'")
        local esfile = r(esfile) 

        * Data in memory is now the coefficient table
        
        * Run coefplot, using the local path `png_outfile`
        capture noisily coefplot, keep(event_*) ///
            vertical xline(0, lpattern(dash)) ciopts(recast(rcap)) ///
            title("Event study: `y'") ytitle("Effect vs rel_year=-1") xtitle("Relative year")
        if _rc==0 graph export "`png_outfile'", replace
        
        restore 
    }
}
*============================*
*         OUTPUT TABLES      *
*============================*
label var post_quake                   "Post"
label var treat_quake                  "Treated (Molise)"

esttab A_* B_* C_* using "$OUT/results_DiD_DDD_dynamic.csv", ///
    replace se r2 ar2 nogap nogaps compress label nonotes ///
    b(%9.4f) se(%9.4f) star(* 0.10 ** 0.05 *** 0.01) ///
    scalars("N N" "r2_a Adj.R2" "model Model" "depvar Outcome")

esttab A_* B_* C_* using "$OUT/results_DiD_DDD_dynamic.txt", ///
    replace se r2 ar2 nogap nogaps label nonotes ///
    b(%9.4f) se(%9.4f) star(* 0.10 ** 0.05 *** 0.01) ///
    title("Designs A/B/C — Region DiD, DDD, and Dynamic DiD")


