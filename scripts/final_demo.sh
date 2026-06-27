#!/usr/bin/env bash
set -euo pipefail

aria config check
aria brain check
aria demo
aria run "Research browser-use and produce a short report for ARIA"
