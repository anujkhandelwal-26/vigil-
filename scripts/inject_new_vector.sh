#!/usr/bin/env bash
# CLI backup for the "new fraud vector" demo beat, in case the UI
# misbehaves on camera. Logs in as $1 (default: analyst), submits the
# held-out BOT_RING_NEW_VECTOR scenario, and prints the risk/anomaly score.
# Usage: ./inject_new_vector.sh [username] [password]
set -euo pipefail
cd "$(dirname "$0")/.."

USERNAME="${1:-analyst}"
set -a; source .env; set +a
PASSWORD="${2:-$VIGIL_DEMO_PASSWORD}"

TOKEN=$(curl -s -X POST http://localhost:8081/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

REF="APP-INJECT-$(date +%s)"
curl -s -X POST http://localhost:8081/api/v1/applications \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d @- <<JSON | python3 -m json.tool
{
  "externalRef": "$REF",
  "age": 29, "gender": "F", "employmentType": "SALARIED", "monthlyIncomeInr": 62000,
  "cityTier": 2, "pincodePrefix": "560", "residenceType": "RENTED",
  "product": "CONSUMER_DURABLE", "amountInr": 85000, "tenureMonths": 12, "channel": "ANDROID_APP",
  "cibilScore": 730, "isNewToCredit": false, "activeLoans": 2, "enquiries30d": 1,
  "maxDpd12m": 0, "creditUtilisationPct": 20, "oldestAccountMonths": 60,
  "panFormatValid": true, "panNameMatchScore": 0.9, "aadhaarPanLinked": true,
  "nameDobMismatch": false, "digilockerDocsFetched": 2, "aadhaarLast4": "4821",
  "deviceHash": "sha256:bot-ring-new-vector-demo", "deviceReuseCount30d": 2, "isEmulator": false,
  "isRooted": true, "appInstallAgeDays": 20, "ipPrefix": "103.21", "ipDistinctApps24h": 4,
  "ipPincodeDistanceKm": 8, "vpnOrProxy": true,
  "formFillSeconds": 25, "typingSpeedCpm": 380, "pasteEvents": 3, "fieldCorrections": 0,
  "sessionScreens": 3, "nightApplication": true, "timeSincePrevAppHours": 1200,
  "bankAccountHash": "sha256:bank-$REF", "pennyDropNameMatch": 0.97, "accountAgeMonths": 42,
  "avgMonthlyCreditInr": 60000, "salaryCreditRegularity": 0.92, "bounceCount6m": 0,
  "accountSharedWithNApplicants": 1,
  "mobileHash": "sha256:mob-$REF", "mobileAgeOnNetworkDays": 820,
  "recentSimSwap30d": false, "mobileNameMatch": 0.96
}
JSON
