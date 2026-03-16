#!/bin/bash
# Show the latest GitHub Actions run for every VBWD-platform repo.
# Usage: ./recipes/ci-status.sh

ORG="VBWD-platform"

# ── Colours ───────────────────────────────────────────────────────────────────
RESET="\033[0m"
BOLD="\033[1m"
DIM="\033[2m"
GREEN="\033[32m"
RED="\033[31m"
YELLOW="\033[33m"
CYAN="\033[36m"
WHITE="\033[37m"

# ── Header ────────────────────────────────────────────────────────────────────
printf "${BOLD}${WHITE}%-45s  %-22s  %-15s  %s${RESET}\n" "REPO" "STATUS/CONCLUSION" "BRANCH" "DATE"
printf "${DIM}%-45s  %-22s  %-15s  %s${RESET}\n"          "----" "-----------------" "------" "----"

# ── Rows ──────────────────────────────────────────────────────────────────────
gh api "orgs/${ORG}/repos?per_page=100" --jq '.[].name' | sort | while read repo; do
  result=$(gh api "repos/${ORG}/${repo}/actions/runs?per_page=1" \
    --jq '.workflow_runs[0] | [.status, .conclusion, .head_branch, (.updated_at | split("T")[0])] | @tsv' 2>/dev/null)

  if [ -z "$result" ]; then
    printf "%-45s  ${DIM}%s${RESET}\n" "$repo" "— no runs"
    continue
  fi

  run_status=$(echo "$result" | cut -f1)
  conclusion=$(echo "$result" | cut -f2)
  branch=$(echo "$result"     | cut -f3)
  date=$(echo "$result"       | cut -f4)

  label="${run_status}/${conclusion}"

  # Colour the status/conclusion cell
  if   [ "$conclusion" = "success" ];    then color="$GREEN"
  elif [ "$conclusion" = "failure" ];    then color="$RED"
  elif [ "$conclusion" = "cancelled" ];  then color="$YELLOW"
  elif [ "$run_status" = "in_progress" ]; then color="$CYAN"
  else                                        color="$DIM"
  fi

  # Dim the repo name for non-main branches
  if [ "$branch" = "main" ]; then repo_color="$WHITE"; else repo_color="$DIM"; fi

  printf "${repo_color}%-45s${RESET}  ${color}%-22s${RESET}  ${DIM}%-15s${RESET}  %s\n" \
    "$repo" "$label" "$branch" "$date"
done
