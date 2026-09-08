# Cohort Audit Log — ADNI 24-Month MCI→AD Progression Study

## Purpose

This document records the cohort-construction decisions, audit findings, and label definitions used for the 24-month MCI→AD progression study. It is intended to serve as the source of truth for Methods, Results, sensitivity analyses, and defense preparation.

## 1. Data sources

Primary diagnostic source:
- `DXSUM_06Sep2026.csv`

Supporting subject-level sources already downloaded:
- `PTDEMOG_06Sep2026.csv`
- `APOERES_06Sep2026.csv`
- `ADNIMERGE2.tar.gz`

The diagnostic timeline is built from DXSUM. Demographic, genetic, and clinical variables will be merged later as baseline predictors.

## 2. Diagnostic-code audit

### Harmonized diagnosis status
- `DIAGNOSIS = 1` → cognitively normal / cognitively unimpaired
- `DIAGNOSIS = 2` → mild cognitive impairment (MCI)
- `DIAGNOSIS = 3` → dementia
- `DIAGNOSIS = 10` → TEAM-phase no-diagnosis / non-usable diagnostic state

Rows without a usable diagnosis or valid exam date are not used as timed diagnostic events.

### Phase-aware AD-event rule

For ADNI1:
- `DIAGNOSIS == 3`
- AND `DXAD == 1`

For ADNIGO / ADNI2 / ADNI3 / ADNI4:
- `DIAGNOSIS == 3`
- AND `DXDDUE == 1`

Dementia rows attributed to non-AD causes are not counted as AD conversion events.

## 3. Initial DXSUM audit

`DXSUM_06Sep2026.csv` contained:
- 16,425 rows
- 41 columns
- 3,757 unique RIDs
- 111 missing/invalid exam dates

Diagnosis distribution:
- `DIAGNOSIS = 1`: 6,636 rows
- `DIAGNOSIS = 2`: 6,650 rows
- `DIAGNOSIS = 3`: 3,047 rows
- `DIAGNOSIS = 10`: 46 rows
- missing diagnosis: 46 rows

Same-RID same-date duplicates were observed, including a very small number of conflicting same-day diagnoses. These were treated as audit issues rather than blindly deduplicated.

## 4. Dementia-cause audit

Among 3,047 dementia rows:
- 1,129 ADNI1 dementia rows had `DXAD = 1`
- 1,841 later-phase dementia rows had `DXDDUE = 1`
- 63 later-phase dementia rows had `DXDDUE = 2`
- 3 ADNI1 dementia rows had `DXOTHDEM = 1`

Later-phase dementia rows with missing `DXDDUE` were separately inspected. Most lacked a valid exam date; the few dated cases had insufficient cause information and were treated as ambiguous rather than automatically counted as AD.

## 5. Baseline MCI construction

Candidate baseline was defined as:
> the first valid dated visit with `DIAGNOSIS == 2` for each subject.

This produced:
- 1,755 subjects with at least one dated MCI visit

Baseline-phase distribution:
- ADNI1: 417
- ADNIGO: 138
- ADNI2: 530
- ADNI3: 384
- ADNI4: 286

## 6. Prior-dementia exclusion

Subjects were audited for any dementia diagnosis before their first candidate MCI baseline.

Result:
- 11 subjects had dementia before the candidate MCI baseline

These subjects were excluded from the clean prognostic baseline cohort because their trajectories represented prior disease / diagnostic reversion rather than a clean at-risk MCI starting state.

After exclusion:
- 1,744 clean MCI baseline candidates remained

## 7. Primary 24-month outcome construction

The prediction horizon is:
> baseline MCI date + 24 calendar months

Primary outcome groups:

### AD converter
A qualifying AD event occurs after baseline and within the 24-month horizon.

### AD non-converter
No qualifying AD event occurs within 24 months and sufficient follow-up reaches at least the 24-month horizon.

### Right-censored
No qualifying AD event is observed, but follow-up ends before the 24-month horizon.

Initial counts:
- 196 AD converters
- 829 initial negatives
- 719 right-censored
- Total: 1,744

Important: right-censored subjects are not assigned a binary negative label because their true 24-month status is unknown.

## 8. Censoring audit

Right-censored subjects:
- 719 total

Follow-up depth among censored subjects:
- 0 days: 349
- 1–6 months: 126
- 6–12 months: 56
- 12–18 months: 153
- 18–24 months: 35

Censoring was especially common in later ADNI phases, particularly ADNI4, consistent with newer recruitment and shorter available follow-up.

## 9. Conversion-timing audit

Primary converters:
- 196

Conversion timing:
- 0–6 months: 9
- 6–12 months: 62
- 12–18 months: 81
- 18–24 months: 44

Median time to AD conversion:
- approximately 391 days

The distribution did not show a suspicious concentration immediately after baseline.

## 10. Converter confirmation and reversion audit

Among the 196 primary converters:
- 152 had a later qualifying AD diagnosis
- 44 did not have later qualifying AD confirmation

Breakdown of the 44 without later confirmation:
- 39 had no post-AD follow-up
- 5 had follow-up but no later qualifying AD diagnosis

### Strict-confirmation definition

Strict converter:
> primary AD conversion within 24 months + at least one later qualifying AD diagnosis

Strict-confirmed converter count:
- 152

### Reversion / diagnostic-instability flag

Among the 196 primary converters:
- 13 later had MCI and/or CN recorded after the AD event
- 183 did not show that reversion pattern

The 13 reverters remain in the primary converter group because they met the predefined primary endpoint. Reversion is treated as an overlapping quality/instability flag rather than as an automatic relabeling rule.

## 11. Negative-trajectory audit

The 829 initial negatives were audited to determine what diagnoses actually occurred within the 24-month window.

Findings:
- 48 had at least one CN visit
- 829 had at least one MCI visit
- 2 had dementia within 24 months

Last diagnosis within the 24-month window:
- 784 ended as MCI
- 43 ended as CN
- 2 ended as dementia

Therefore, the label name `stable_mci` was judged too strong because some negatives reverted to CN.

Preferred terminology:
> 24-month AD non-converter

## 12. Non-AD dementia competing events

Two initial negatives developed dementia within the 24-month window but were not AD events under the cause-specific rule.

### RID 2398
- baseline MCI: 2011-07-14
- dementia visit: 2012-07-25
- `DIAGNOSIS = 3`
- `DXDDUE = 2`

### RID 4637
- baseline MCI: 2021-12-06
- dementia visits: 2022-10-25 and 2023-10-10
- `DIAGNOSIS = 3`
- `DXDDUE = 2`

These are non-AD dementia competing events, not ordinary AD non-converters.

Recommended primary-binary treatment:
- exclude these 2 from the clean binary classification cohort
- document them explicitly as competing-event exclusions

This would yield the clean primary binary cohort:
- 196 AD converters
- 827 AD non-converters
- 719 right-censored
- 2 non-AD dementia competing-event exclusions

## 13. Binary-label definitions

### Primary binary label
- AD converter → `1`
- clean AD non-converter → `0`
- right-censored → missing / excluded from binary training
- non-AD dementia competing event → excluded from primary binary training

### Strict sensitivity label
- strict-confirmed AD converter → `1`
- clean AD non-converter → `0`
- primary converter without later AD confirmation → missing for strict sensitivity analysis
- right-censored → missing
- non-AD dementia competing event → excluded

## 14. Current methodological rationale

1. Fixed 24-month horizon
   - creates a specific prognosis question
   - limits loss to long-term follow-up
   - avoids mixing short- and long-term progression

2. First valid MCI visit as baseline
   - prevents selecting a later MCI visit that may be closer to conversion
   - reduces temporal-selection bias

3. Prior dementia exclusion
   - avoids prevalent-disease contamination
   - ensures a clean at-risk MCI cohort

4. Right-censoring
   - prevents short-follow-up participants from being mislabeled as negatives
   - preserves label validity

5. Phase-aware AD-event definition
   - respects changes in ADNI diagnostic variables across study phases
   - prevents all-cause dementia from being mislabeled as AD

6. Primary vs strict converter definitions
   - allows sensitivity analysis for diagnostic instability
   - tests whether model conclusions depend on one potentially unstable AD diagnosis

7. Reversion flagging
   - preserves primary endpoint integrity
   - explicitly captures AD→MCI/CN diagnostic instability

8. Competing-event handling
   - prevents non-AD dementia from being treated as ordinary non-conversion
   - keeps the binary target specific to MCI→AD progression

## 15. Current status

Cohort definition is nearly complete.

Remaining work before final cohort freeze:
- update the cohort-building script to:
  - rename `stable_mci` to `ad_non_converter`
  - flag the 2 non-AD dementia competing events
  - exclude those 2 from primary binary training
- regenerate the final processed cohort file
- rerun all assertions and counts
- then proceed to demographics, APOE, clinical-feature merging, missingness analysis, and MRI matching

## 16. Defense-ready summary

> We constructed a 24-month MCI-to-AD prognostic cohort using longitudinal ADNI diagnosis data. We used the first valid MCI visit as baseline, excluded participants with prior dementia, applied phase-specific ADNI fields to distinguish AD from other dementia etiologies, treated incomplete follow-up as right-censoring rather than non-conversion, and performed a stricter confirmation-based sensitivity analysis to assess diagnostic-label robustness. We also audited post-conversion reversions and non-AD dementia competing events before model development.
