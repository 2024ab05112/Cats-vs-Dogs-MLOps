#!/usr/bin/env bash
# smoke_test.sh — Post-deployment health validation (M4 requirement)
# Fails the pipeline if any critical endpoint is unreachable.

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
MAX_RETRIES=12
SLEEP_SEC=10

echo "================================================"
echo "  Post-Deploy Smoke Test"
echo "  Target: $BASE_URL"
echo "================================================"

check_endpoint() {
    local endpoint="$1"
    local expected_code="$2"
    local label="$3"
    local retries=0

    echo ""
    echo ">> Checking: $label ($BASE_URL$endpoint)"

    while [ "$retries" -lt "$MAX_RETRIES" ]; do
        code=$(curl -sk -o /dev/null -w "%{http_code}" "${BASE_URL}${endpoint}" || true)

        if [ "$code" -eq "$expected_code" ]; then
            echo "   [PASS] HTTP $code"
            return 0
        fi

        echo "   [WAIT] Got $code, expected $expected_code — attempt $((retries+1))/$MAX_RETRIES"
        sleep "$SLEEP_SEC"
        retries=$((retries+1))
    done

    echo "   [FAIL] $label did not return $expected_code after $MAX_RETRIES attempts"
    return 1
}

# 1. Backend health check
check_endpoint "/health" 200 "Backend Health"

# 2. Swagger docs (verifies API is fully initialized)
check_endpoint "/docs" 200 "API Documentation (Swagger)"

# 3. Metrics endpoint (verifies Prometheus integration)
check_endpoint "/api/metrics" 200 "Prometheus Metrics"

echo ""
echo "================================================"
echo "  ALL SMOKE TESTS PASSED ✓"
echo "================================================"
exit 0
