cd ~/FastSurfer-stable

cat > verify_surfaces.py <<'PY'
#!/usr/bin/env python3

from pathlib import Path
import sys
import numpy as np
from nibabel.freesurfer.io import read_geometry, read_morph_data, read_annot

if len(sys.argv) != 2:
    print("Usage: python verify_surfaces.py /path/to/TEST001")
    sys.exit(2)

subject = Path(sys.argv[1])
failed = False

def fail(msg):
    global failed
    failed = True
    print(f"❌ {msg}")

def passed(msg):
    print(f"✅ {msg}")

for hemi in ("lh", "rh"):
    print(f"\n--- {hemi.upper()} ---")

    white_file = subject / "surf" / f"{hemi}.white"
    pial_file = subject / "surf" / f"{hemi}.pial"
    thickness_file = subject / "surf" / f"{hemi}.thickness"
    area_file = subject / "surf" / f"{hemi}.area"
    annot_file = subject / "label" / f"{hemi}.aparc.DKTatlas.mapped.annot"

    try:
        white_vertices, white_faces = read_geometry(white_file)
        passed(f"{hemi}.white readable")
    except Exception as e:
        fail(f"{hemi}.white unreadable: {e}")
        continue

    try:
        pial_vertices, pial_faces = read_geometry(pial_file)
        passed(f"{hemi}.pial readable")
    except Exception as e:
        fail(f"{hemi}.pial unreadable: {e}")
        continue

    try:
        thickness = read_morph_data(thickness_file)
        passed(f"{hemi}.thickness readable")
    except Exception as e:
        fail(f"{hemi}.thickness unreadable: {e}")
        continue

    try:
        area = read_morph_data(area_file)
        passed(f"{hemi}.area readable")
    except Exception as e:
        fail(f"{hemi}.area unreadable: {e}")
        continue

    try:
        labels, ctab, names = read_annot(annot_file)
        passed(f"{hemi} DKT annotation readable")
    except Exception as e:
        fail(f"{hemi} DKT annotation unreadable: {e}")
        continue

    n = len(white_vertices)

    if len(pial_vertices) == n:
        passed(f"{hemi} white/pial vertex counts agree ({n})")
    else:
        fail(f"{hemi} white/pial vertex mismatch")

    if len(thickness) == n:
        passed(f"{hemi} thickness vertex count agrees")
    else:
        fail(f"{hemi} thickness length mismatch")

    if len(area) == n:
        passed(f"{hemi} area vertex count agrees")
    else:
        fail(f"{hemi} area length mismatch")

    if len(labels) == n:
        passed(f"{hemi} DKT annotation vertex count agrees")
    else:
        fail(f"{hemi} annotation length mismatch")

    if np.isfinite(thickness).all():
        passed(f"{hemi} thickness has no NaN/Inf")
    else:
        fail(f"{hemi} thickness contains NaN/Inf")

    if np.isfinite(area).all():
        passed(f"{hemi} area has no NaN/Inf")
    else:
        fail(f"{hemi} area contains NaN/Inf")

print("\n========================================")

if failed:
    print("❌ SURFACE INTEGRITY CHECK: FAIL")
    sys.exit(1)
else:
    print("✅ SURFACE INTEGRITY CHECK: PASS")
    sys.exit(0)
PY