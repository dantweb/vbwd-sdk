#!/bin/bash
set -e

# Push all plugin source directories to their VBWD-platform repos.
# Run after review. Idempotent — safe to re-run.
#
# Usage: ./recipes/push-plugins.sh
#        ./recipes/push-plugins.sh ghrm          # push single backend plugin
#        ./recipes/push-plugins.sh fe-user chat   # push single fe-user plugin

push_plugin() {
  local dir="$1"
  local repo="$2"    # e.g. VBWD-platform/vbwd-plugin-ghrm
  local msg="${3:-initial: publish plugin source}"

  echo ""
  echo "── $repo"

  cd "$dir"

  # Stage everything (respects .gitignore)
  git add -A

  # Only commit if there's something staged
  if git diff --cached --quiet; then
    echo "  nothing to commit"
  else
    git commit -m "$msg"
  fi

  # Force-push: remote has only an auto-generated README commit from repo
  # creation; our local source is authoritative.
  git push -u origin main --force

  echo "  ✓ pushed"
  cd - > /dev/null
}

BACKEND="$(cd "$(dirname "$0")/../vbwd-backend" && pwd)"
FE_USER="$(cd "$(dirname "$0")/../vbwd-fe-user" && pwd)"
FE_ADMIN="$(cd "$(dirname "$0")/../vbwd-fe-admin" && pwd)"

# Filter mode: single plugin
if [ -n "$1" ]; then
  case "$1" in
    fe-user)
      push_plugin "$FE_USER/plugins/$2" "VBWD-platform/vbwd-fe-user-plugin-$2"
      exit 0
      ;;
    fe-admin)
      push_plugin "$FE_ADMIN/plugins/$2" "VBWD-platform/vbwd-fe-admin-plugin-$2"
      exit 0
      ;;
    *)
      push_plugin "$BACKEND/plugins/$1" "VBWD-platform/vbwd-plugin-$1"
      exit 0
      ;;
  esac
fi

# ── Backend plugins ───────────────────────────────────────────────────────────
echo "=== Backend plugins ==="
for plugin in analytics chat cms email ghrm mailchimp paypal stripe taro yookassa; do
  push_plugin "$BACKEND/plugins/$plugin" "VBWD-platform/vbwd-plugin-$plugin"
done

# ── fe-user plugins ───────────────────────────────────────────────────────────
echo ""
echo "=== fe-user plugins ==="
for slug in chat checkout cms ghrm landing1 paypal-payment stripe-payment taro theme-switcher yookassa-payment; do
  push_plugin "$FE_USER/plugins/$slug" "VBWD-platform/vbwd-fe-user-plugin-$slug"
done

# ── fe-admin plugins ──────────────────────────────────────────────────────────
echo ""
echo "=== fe-admin plugins ==="
for slug in analytics-widget cms-admin email-admin ghrm-admin taro-admin; do
  push_plugin "$FE_ADMIN/plugins/$slug" "VBWD-platform/vbwd-fe-admin-plugin-$slug"
done

echo ""
echo "Done. All plugins pushed."
