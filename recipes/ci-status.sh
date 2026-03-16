#!/bin/bash
# Show the latest GitHub Actions run for every VBWD-platform repo.
# Usage: ./recipes/ci-status.sh

ORG="VBWD-platform"

printf "%-45s  %-22s  %-15s  %s\n" "REPO" "STATUS/CONCLUSION" "BRANCH" "DATE"
printf "%-45s  %-22s  %-15s  %s\n" "----" "-----------------" "------" "----"

gh api "orgs/${ORG}/repos?per_page=100" --jq '.[].name' | sort | while read repo; do
  result=$(gh api "repos/${ORG}/${repo}/actions/runs?per_page=1" \
    --jq '.workflow_runs[0] | [.status, .conclusion, .head_branch, (.updated_at | split("T")[0])] | @tsv' 2>/dev/null)
  if [ -z "$result" ]; then
    printf "%-45s  %s\n" "$repo" "— no runs"
  else
    run_status=$(echo "$result" | cut -f1)
    conclusion=$(echo "$result" | cut -f2)
    branch=$(echo "$result" | cut -f3)
    date=$(echo "$result" | cut -f4)
    printf "%-45s  %-22s  %-15s  %s\n" "$repo" "${run_status}/${conclusion}" "$branch" "$date"
  fi
done
