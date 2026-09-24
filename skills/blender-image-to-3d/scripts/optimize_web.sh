#!/usr/bin/env bash
# Compress a delivered GLB for web targets (crazygames, astrocade, spawn, threejs).
# Usage: optimize_web.sh <in.glb> <out.glb> <profile> [--rigged]
#   profile: crazygames | astrocade | spawn | threejs
#   --rigged: keep node and material structure and empty nodes. Use it for skinned meshes AND for
#   anything with SOCKET_ empties, pivots or parts looked up by name (default prune deletes empties)
# Needs: npx (Node 18+). KTX2 needs KTX-Software `toktx` on PATH; without it WebP is used.
set -euo pipefail
IN="$1"; OUT="$2"; PROFILE="${3:-threejs}"; RIGGED="${4:-}"
GT="npx -y @gltf-transform/cli@4"
case "$PROFILE" in
  astrocade) SIZE=1024; TEX=webp ;;           # three r128: meshopt + webp, avoid KTX2
  spawn)     SIZE=1024; TEX=webp ;;           # CDN recompresses; keep it simple
  crazygames) SIZE=2048; TEX=auto ;;
  *)         SIZE=2048; TEX=auto ;;
esac
if [ "$TEX" = auto ]; then
  if command -v toktx >/dev/null 2>&1; then TEX=ktx2; else TEX=webp; fi
fi
KEEP=""
if [ "$RIGGED" = "--rigged" ]; then
  KEEP="--flatten false --join false --palette false --instance false --prune false"
fi
# simplify stays off: triangle budgets are met in Phase 4 by hand, not by a blind simplifier
$GT optimize "$IN" "$OUT" --compress meshopt --texture-compress "$TEX" --texture-size "$SIZE" \
  --simplify false $KEEP
echo "optimized $IN -> $OUT ($PROFILE, textures $TEX <= ${SIZE}px)"
ls -l "$IN" "$OUT" | awk '{print $5, $9}'
