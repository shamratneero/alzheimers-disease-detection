#!/usr/bin/env bash

SUBJ="${1:-}"

if [[ -z "$SUBJ" ]]; then
    echo "Usage:"
    echo "  bash verify_fastsurfer.sh /path/to/TEST001"
    exit 2
fi

FAIL=0
WARN=0

pass() { echo "✅ $1"; }
fail() { echo "❌ $1"; FAIL=1; }
warn() { echo "⚠️  $1"; WARN=$((WARN+1)); }

check_file() {
    local f="$SUBJ/$1"

    if [[ -s "$f" ]]; then
        pass "$1"
    else
        fail "$1 MISSING OR EMPTY"
    fi
}

echo
echo "========================================"
echo " FastSurfer Full-Pipeline Verification"
echo "========================================"
echo
echo "Subject directory:"
echo "$SUBJ"
echo

echo "---- Core MRI outputs ----"

check_file "mri/orig.mgz"
check_file "mri/orig_nu.mgz"
check_file "mri/aseg.mgz"
check_file "mri/aparc.DKTatlas+aseg.mapped.mgz"
check_file "mri/brain.finalsurfs.mgz"
check_file "mri/wm.mgz"
check_file "mri/filled.mgz"

echo
echo "---- Left hemisphere surfaces ----"

check_file "surf/lh.white"
check_file "surf/lh.pial"
check_file "surf/lh.thickness"
check_file "surf/lh.area"
check_file "surf/lh.inflated"

echo
echo "---- Right hemisphere surfaces ----"

check_file "surf/rh.white"
check_file "surf/rh.pial"
check_file "surf/rh.thickness"
check_file "surf/rh.area"
check_file "surf/rh.inflated"

echo
echo "---- Cortical annotations ----"

check_file "label/lh.aparc.DKTatlas.mapped.annot"
check_file "label/rh.aparc.DKTatlas.mapped.annot"

echo
echo "---- Statistics ----"

check_file "stats/aseg.stats"
check_file "stats/lh.aparc.DKTatlas.mapped.stats"
check_file "stats/rh.aparc.DKTatlas.mapped.stats"

echo
echo "---- Logs ----"

check_file "scripts/deep-seg.log"
check_file "scripts/recon-surf.log"

LOG="$SUBJ/scripts/recon-surf.log"

echo
echo "---- Surface log inspection ----"

if [[ -f "$LOG" ]]; then

    if grep -Eqi \
        'ModuleNotFoundError|Traceback \(most recent call last\)|ERROR: could not|FATAL|exited with ERRORS|finished with exit code [1-9]' \
        "$LOG"
    then
        fail "Fatal-looking error found in recon-surf.log"

        echo
        echo "Relevant log lines:"
        grep -Ei \
            'ModuleNotFoundError|Traceback \(most recent call last\)|ERROR: could not|FATAL|exited with ERRORS|finished with exit code [1-9]' \
            "$LOG" | tail -20
    else
        pass "No fatal error pattern found in recon-surf.log"
    fi

    if grep -qi "finished without error" "$LOG"; then
        pass "FreeSurfer completion marker found"
    else
        warn "'finished without error' marker not found"
    fi

else
    fail "recon-surf.log missing"
fi

echo
echo "---- Research-critical anatomy checks ----"

LH="$SUBJ/stats/lh.aparc.DKTatlas.mapped.stats"
RH="$SUBJ/stats/rh.aparc.DKTatlas.mapped.stats"
ASEG="$SUBJ/stats/aseg.stats"

if grep -qi "entorhinal" "$LH" 2>/dev/null; then
    pass "Left entorhinal cortical stats present"
else
    fail "Left entorhinal stats missing"
fi

if grep -qi "entorhinal" "$RH" 2>/dev/null; then
    pass "Right entorhinal cortical stats present"
else
    fail "Right entorhinal stats missing"
fi

if grep -qi "Left-Hippocampus" "$ASEG" 2>/dev/null; then
    pass "Left hippocampus stats present"
else
    fail "Left hippocampus stats missing"
fi

if grep -qi "Right-Hippocampus" "$ASEG" 2>/dev/null; then
    pass "Right hippocampus stats present"
else
    fail "Right hippocampus stats missing"
fi

if grep -Eqi 'EstimatedTotalIntraCranialVol|eTIV' "$ASEG" 2>/dev/null; then
    pass "eTIV / intracranial-volume measure present"
else
    warn "Could not find eTIV in aseg.stats"
fi

echo
echo "========================================"

if [[ "$FAIL" -eq 0 ]]; then
    echo "✅ FULL PIPELINE FILE CHECK: PASS"

    if [[ "$WARN" -gt 0 ]]; then
        echo "⚠️  Warnings: $WARN"
    fi

    exit 0
else
    echo "❌ FULL PIPELINE FILE CHECK: FAIL"
    exit 1
fi