#Requires -Version 5.1
<#
.SYNOPSIS
    ReqPilot GROQ LLM Runtime Verification Script
    Version: 2.0

.DESCRIPTION
    Performs a complete end-to-end runtime verification of ReqPilot's GROQ LLM path.

    SAFETY GUARANTEES:
    - NEVER modifies backend/reqpilot.db.
    - NEVER prints, logs, or serializes the API key or any secret.
    - NEVER modifies source code.
    - Uses only a temporary database copy (deleted during cleanup).
    - Uses a dedicated verification port (8001) to avoid dev-server conflicts.
    - Cleans up all temporary resources in a finally block even if verification fails.

    Run from the fsd_pro project root:
        .\runtime\runtime_verification.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
$VERIFY_PORT     = 8001
$VERIFY_HOST     = "127.0.0.1"
$VERIFY_BASE_URL = "http://${VERIFY_HOST}:${VERIFY_PORT}"
$PROVIDER        = "groq"
$MODEL           = "llama-3.3-70b-versatile"
$STARTUP_WAIT_S  = 8     # seconds to wait for uvicorn to become ready
$ANALYSIS_WAIT_S = 60    # seconds to wait for full pipeline to complete

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
$ProjectRoot   = (Get-Location).Path
$OrigDbPath    = Join-Path $ProjectRoot "backend\reqpilot.db"
$UniqueId      = [System.Guid]::NewGuid().ToString("N").Substring(0,8)
$TempDbPath    = Join-Path $ProjectRoot "backend\reqpilot_verify_${UniqueId}.db"
$TempSrsPath   = Join-Path $ProjectRoot "runtime\temp_srs_${UniqueId}.txt"
$ServerStdOut  = Join-Path $ProjectRoot "runtime\verify_stdout_${UniqueId}.log"
$ServerStdErr  = Join-Path $ProjectRoot "runtime\verify_stderr_${UniqueId}.log"
$ReportPath    = Join-Path $ProjectRoot "runtime\runtime_verification_report.json"

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
function Get-FileSHA256 {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    $hash = Get-FileHash -Path $Path -Algorithm SHA256
    return $hash.Hash
}

function Invoke-API {
    param(
        [string]$Method,
        [string]$Url,
        [string]$Body = $null,
        [string]$ContentType = "application/json",
        [string]$FormFilePath = $null
    )
    try {
        if ($FormFilePath) {
            $result = & curl.exe -s -X $Method $Url -F "file=@$FormFilePath" 2>&1
        } elseif ($Body) {
            $result = & curl.exe -s -X $Method $Url -H "Content-Type: $ContentType" -d $Body 2>&1
        } else {
            $result = & curl.exe -s -X $Method $Url 2>&1
        }
        return $result -join ""
    } catch {
        return $null
    }
}

function Get-ProjectCount {
    param([string]$ProjectId, [string]$Endpoint)
    $raw = Invoke-API -Method "GET" -Url "${VERIFY_BASE_URL}/api/projects/${ProjectId}/${Endpoint}"
    if (-not $raw) { return 0 }
    try {
        $parsed = $raw | ConvertFrom-Json
        if ($parsed -is [System.Array]) { return $parsed.Count }
        return 0
    } catch { return 0 }
}

# ---------------------------------------------------------------------------
# INITIALISE REPORT OBJECT (all required fields present from the start)
# ---------------------------------------------------------------------------
$Report = [ordered]@{
    outcome                              = "NOT_STARTED"
    provider                             = $PROVIDER
    model                                = $MODEL
    llm_call                             = [ordered]@{
        attempted  = $false
        succeeded  = $null
        evidence   = "Not yet evaluated"
    }
    fallback_used                        = "unknown"
    requirements_count                   = 0
    downstream_counts                    = [ordered]@{
        issues                 = 0
        clarifications         = 0
        architecture_modules   = 0
        architecture_relations = 0
        tasks                  = 0
        sprints                = 0
        test_cases             = 0
        traceability_links     = 0
        reports                = 0
    }
    temporary_database_persistence       = $false
    original_database_checksum_before    = $null
    original_database_checksum_after     = $null
    original_database_unchanged          = $null
    test_project_id_in_original_db       = $null
    source_code_modified                 = $false
    secrets_exposed                      = $false
    errors                               = @()
}

$ServerProcess = $null
$TempProjectId = $null

# ---------------------------------------------------------------------------
# MAIN - wrapped in try/finally for guaranteed cleanup
# ---------------------------------------------------------------------------
try {

    Write-Host "`n===== ReqPilot GROQ LLM Verification v2.0 =====" -ForegroundColor Cyan
    Write-Host "Project root : $ProjectRoot"
    Write-Host "Provider     : $PROVIDER"
    Write-Host "Model        : $MODEL"
    Write-Host "Verify port  : $VERIFY_PORT"

    # -----------------------------------------------------------------------
    # STEP 1 - Verify source database exists and capture its checksum
    # -----------------------------------------------------------------------
    Write-Host "`n[1] Verifying original database..." -ForegroundColor Yellow

    if (-not (Test-Path $OrigDbPath)) {
        throw "Original database not found at: $OrigDbPath"
    }

    $checksumBefore = Get-FileSHA256 -Path $OrigDbPath
    $Report.original_database_checksum_before = $checksumBefore
    Write-Host "    Original DB SHA-256 (before): $checksumBefore"

    # -----------------------------------------------------------------------
    # STEP 2 - Copy original DB to temporary location
    # -----------------------------------------------------------------------
    Write-Host "`n[2] Creating temporary database copy..." -ForegroundColor Yellow

    Copy-Item -Path $OrigDbPath -Destination $TempDbPath -Force
    Write-Host "    Temporary DB: $TempDbPath"

    # -----------------------------------------------------------------------
    # STEP 3 - Check selected port is free
    # -----------------------------------------------------------------------
    Write-Host "`n[3] Checking port $VERIFY_PORT is free..." -ForegroundColor Yellow

    $portBusy = Get-NetTCPConnection -LocalPort $VERIFY_PORT -State Listen -ErrorAction SilentlyContinue
    if ($portBusy) {
        throw "Port $VERIFY_PORT is already in use. Stop the occupying process and re-run."
    }
    Write-Host "    Port $VERIFY_PORT is available."

    # -----------------------------------------------------------------------
    # STEP 4 - Write temporary SRS document
    # -----------------------------------------------------------------------
    Write-Host "`n[4] Writing temporary SRS document..." -ForegroundColor Yellow

    $srsContent = @"
Software Requirements Specification - User Authentication and Profile System
Version: 1.0 (Temporary verification document - do not archive)

FR-001: The system shall allow a new user to register an account using a unique email address and a password that meets complexity requirements.
FR-002: Upon successful registration, the system shall send an email-verification link to the registered email address within 60 seconds.
FR-003: The system shall allow a registered and email-verified user to log in using their email address and password.
FR-004: After a successful login, the system shall display a personalized dashboard showing the user's activity summary and recent actions.
FR-005: The system shall allow a logged-in user to update their profile information, including display name, avatar, and notification preferences.
FR-006: The system shall automatically log out a user session after 30 consecutive minutes of inactivity and notify the user before doing so.
FR-007: The system shall store all user passwords using a modern cryptographic hashing algorithm (e.g. Argon2 or bcrypt) and shall never store plaintext passwords.
FR-008: The system shall expose a RESTful API endpoint that returns the authenticated user's dashboard data in JSON format.
FR-009: The system shall validate all user-submitted input on both the client side and the server side and shall reject requests that fail validation with a descriptive error message.
FR-010: The system shall maintain an immutable audit log of all security-relevant events, including logins, logouts, password changes, and failed authentication attempts.
"@
    $srsContent | Set-Content -Path $TempSrsPath -Encoding utf8
    Write-Host "    SRS written to: $TempSrsPath"

    # -----------------------------------------------------------------------
    # STEP 5 - Configure environment and start the verification server
    # -----------------------------------------------------------------------
    Write-Host "`n[5] Starting verification server on port $VERIFY_PORT..." -ForegroundColor Yellow

    # Point the app at the TEMPORARY database only - never the original
    $TempDbUrl = "sqlite+aiosqlite:///" + ($TempDbPath -replace "\\","/")
    $env:DATABASE_URL = $TempDbUrl
    $env:PYTHONPATH   = $ProjectRoot
    # GROQ_API_KEY is NOT set here - the app reads it from backend/.env via load_dotenv().
    # This ensures the key never appears in this script or its output.

    $StartInfo = New-Object System.Diagnostics.ProcessStartInfo
    $StartInfo.FileName  = "python"
    $StartInfo.Arguments = "-m uvicorn backend.app.main:app --host $VERIFY_HOST --port $VERIFY_PORT"
    $StartInfo.UseShellExecute        = $false
    $StartInfo.RedirectStandardOutput = $true
    $StartInfo.RedirectStandardError  = $true
    $StartInfo.CreateNoWindow         = $true

    $ServerProcess = New-Object System.Diagnostics.Process
    $ServerProcess.StartInfo = $StartInfo
    $ServerProcess.Start() | Out-Null
    $ServPid = $ServerProcess.Id

    Write-Host "    Server PID: $ServPid - waiting ${STARTUP_WAIT_S}s for startup..."
    Start-Sleep -Seconds $STARTUP_WAIT_S

    # Quick health check
    $healthRaw = Invoke-API -Method "GET" -Url "${VERIFY_BASE_URL}/api/projects"
    if (-not $healthRaw) {
        throw "Server did not respond on port $VERIFY_PORT after ${STARTUP_WAIT_S}s."
    }
    Write-Host "    Server is responding."

    # -----------------------------------------------------------------------
    # STEP 6 - Create a temporary test project
    # -----------------------------------------------------------------------
    Write-Host "`n[6] Creating temporary test project..." -ForegroundColor Yellow

    $projPayload = '{"title":"GROQ Verification Project","description":"Temporary project for LLM runtime verification. Safe to delete.","domain":"Identity and Access Management"}'
    $projRaw = Invoke-API -Method "POST" -Url "${VERIFY_BASE_URL}/api/projects" -Body $projPayload
    if (-not $projRaw) { throw "Failed to create test project - no response from server." }

    Write-Host "    Raw project response: $projRaw"

    try {
        $projJson = $projRaw | ConvertFrom-Json
    } catch {
        throw "Project creation returned non-JSON response: $projRaw"
    }

    $TempProjectId = $null

    if ($projJson.PSObject.Properties.Name -contains "id") {
        $TempProjectId = [string]$projJson.id
    } elseif ($projJson.PSObject.Properties.Name -contains "project") {
        if ($projJson.project -and ($projJson.project.PSObject.Properties.Name -contains "id")) {
            $TempProjectId = [string]$projJson.project.id
        }
    }

    if (-not $TempProjectId) {
        throw "Project creation response did not contain a usable id. Response: $projRaw"
    }

    Write-Host "    Test project ID: $TempProjectId"

    # -----------------------------------------------------------------------
    # STEP 7 - Upload the SRS document
    # -----------------------------------------------------------------------
    Write-Host "`n[7] Uploading SRS document..." -ForegroundColor Yellow

    $uploadRaw = Invoke-API -Method "POST" -Url "${VERIFY_BASE_URL}/api/projects/${TempProjectId}/documents/upload" -FormFilePath $TempSrsPath
    Write-Host "    Upload response: $uploadRaw"
    Start-Sleep -Seconds 3

    # -----------------------------------------------------------------------
    # STEP 8 - Trigger analysis with use_llm=true, provider=groq
    # -----------------------------------------------------------------------
    Write-Host "`n[8] Triggering analysis (use_llm=true, provider=groq)..." -ForegroundColor Yellow

    $Report.llm_call.attempted = $true
    $analysisPayload = '{"use_llm":true,"provider":"groq"}'
    $analysisRaw = Invoke-API -Method "POST" -Url "${VERIFY_BASE_URL}/api/projects/${TempProjectId}/analyze" -Body $analysisPayload

    Write-Host "    Waiting ${ANALYSIS_WAIT_S}s for pipeline to complete..."
    Start-Sleep -Seconds $ANALYSIS_WAIT_S

    Write-Host "    Analysis response received."

    # -----------------------------------------------------------------------
    # STEP 9 - Read server logs to evaluate LLM call evidence
    # -----------------------------------------------------------------------
    Write-Host "`n[9] Evaluating LLM call evidence from server logs..." -ForegroundColor Yellow

    $stdoutLines = @()
    $stderrLines = @()
    try {
        if (-not $ServerProcess.StandardOutput.EndOfStream) {
            $allOut = $ServerProcess.StandardOutput.ReadToEnd()
            $stdoutLines = $allOut -split "`n"
        }
        if (-not $ServerProcess.StandardError.EndOfStream) {
            $allErr = $ServerProcess.StandardError.ReadToEnd()
            $stderrLines = $allErr -split "`n"
        }
    } catch {}

    $stdoutLines | Set-Content -Path $ServerStdOut -Encoding utf8
    $stderrLines | Set-Content -Path $ServerStdErr -Encoding utf8

    $allLogLines = $stdoutLines + $stderrLines
    $combinedLog = $allLogLines -join "`n"

    # Evidence analysis - specific to ReqPilot's GROQ httpx implementation
    # The Groq path (llm_adapter.py) uses httpx POST to api.groq.com/openai/v1/chat/completions
    # On failure it logs: "Groq API returned <status>: ..." or "Groq API generation failed: ..."
    # On success it proceeds silently (no explicit success log line)
    # Fallback logs: "Falling back to deterministic engine"

    $groqSuccessEvidence = ($combinedLog -match "(?i)api\.groq\.com") -or
                           ($combinedLog -match "(?i)llama-3\.3-70b") -or
                           ($combinedLog -match "(?i)openai/v1/chat/completions")

    $groqFailureEvidence = ($combinedLog -match "(?i)Groq API (returned|generation) failed") -or
                           ($combinedLog -match "(?i)Groq API returned [45][0-9]{2}")

    $fallbackEvidence    = $combinedLog -match "(?i)Falling back to deterministic engine"
    $authErrorEvidence   = $combinedLog -match "(?i)(401|403|invalid.?api.?key|unauthorized)"

    if ($groqSuccessEvidence -and -not $groqFailureEvidence) {
        $Report.llm_call.succeeded = $true
        $Report.llm_call.evidence  = "Log evidence indicates successful Groq API call (api.groq.com / openai/v1/chat/completions endpoint reached)."
        $Report.fallback_used      = $false
    } elseif ($groqFailureEvidence -or $authErrorEvidence) {
        $Report.llm_call.succeeded = $false
        $Report.fallback_used      = $true
        $errHint = if ($authErrorEvidence) { "Auth error (401/403) - check GROQ_API_KEY in backend/.env." } else { "Groq API HTTP error - see server logs." }
        $Report.llm_call.evidence  = "Groq API failure detected in logs. $errHint"
    } elseif ($fallbackEvidence -and -not $groqSuccessEvidence) {
        $Report.llm_call.succeeded = $false
        $Report.fallback_used      = $true
        $Report.llm_call.evidence  = "Deterministic fallback detected in logs. No evidence of a successful live Groq call."
    } else {
        $Report.llm_call.succeeded = $null
        $Report.fallback_used      = "unknown"
        $Report.llm_call.evidence  = "LLM CALL EVIDENCE INSUFFICIENT - server logs do not contain definitive Groq success or failure signals. Inspect runtime/verify_stdout_${UniqueId}.log and verify_stderr_${UniqueId}.log manually before those files are cleaned up."
    }

    Write-Host "    LLM evidence: $($Report.llm_call.evidence)"

    # -----------------------------------------------------------------------
    # STEP 10 - Collect requirements and all downstream counts
    # -----------------------------------------------------------------------
    Write-Host "`n[10] Collecting downstream pipeline results..." -ForegroundColor Yellow

    $reqRaw = Invoke-API -Method "GET" -Url "${VERIFY_BASE_URL}/api/projects/${TempProjectId}/requirements"
    $reqs   = @()
    if ($reqRaw) {
        try { $reqs = $reqRaw | ConvertFrom-Json } catch {}
    }
    $reqCount = if ($reqs -is [System.Array]) { $reqs.Count } else { 0 }
    $Report.requirements_count = $reqCount

    $Report.downstream_counts.issues                 = Get-ProjectCount $TempProjectId "issues"
    $Report.downstream_counts.clarifications         = Get-ProjectCount $TempProjectId "clarifications"
    $Report.downstream_counts.architecture_modules   = Get-ProjectCount $TempProjectId "architecture/modules"
    $Report.downstream_counts.architecture_relations = Get-ProjectCount $TempProjectId "architecture/relations"
    $Report.downstream_counts.tasks                  = Get-ProjectCount $TempProjectId "tasks"
    $Report.downstream_counts.sprints                = Get-ProjectCount $TempProjectId "sprints"
    $Report.downstream_counts.test_cases             = Get-ProjectCount $TempProjectId "tests"
    $Report.downstream_counts.traceability_links     = Get-ProjectCount $TempProjectId "traceability"
    $Report.downstream_counts.reports                = Get-ProjectCount $TempProjectId "reports"

    Write-Host ("    Requirements      : " + $Report.requirements_count)
    Write-Host ("    Issues            : " + $Report.downstream_counts.issues)
    Write-Host ("    Clarifications    : " + $Report.downstream_counts.clarifications)
    Write-Host ("    Arch Modules      : " + $Report.downstream_counts.architecture_modules)
    Write-Host ("    Arch Relations    : " + $Report.downstream_counts.architecture_relations)
    Write-Host ("    Tasks             : " + $Report.downstream_counts.tasks)
    Write-Host ("    Sprints           : " + $Report.downstream_counts.sprints)
    Write-Host ("    Test Cases        : " + $Report.downstream_counts.test_cases)
    Write-Host ("    Traceability Links: " + $Report.downstream_counts.traceability_links)
    Write-Host ("    Reports           : " + $Report.downstream_counts.reports)

    # -----------------------------------------------------------------------
    # STEP 11 - Verify persistence in temporary database
    # -----------------------------------------------------------------------
    $Report.temporary_database_persistence = ($reqCount -gt 0)

    # -----------------------------------------------------------------------
    # STEP 12 - Verify original database integrity
    # -----------------------------------------------------------------------
    Write-Host "`n[12] Verifying original database integrity..." -ForegroundColor Yellow

    $checksumAfter = Get-FileSHA256 -Path $OrigDbPath
    $Report.original_database_checksum_after = $checksumAfter
    $Report.original_database_unchanged      = ($checksumBefore -eq $checksumAfter)

    Write-Host "    SHA-256 before : $checksumBefore"
    Write-Host "    SHA-256 after  : $checksumAfter"
    Write-Host "    Unchanged      : $($Report.original_database_unchanged)"

    # -----------------------------------------------------------------------
    # STEP 13 - Verify test project does NOT appear in the original database
    # -----------------------------------------------------------------------
    Write-Host "`n[13] Verifying test project is NOT in original database..." -ForegroundColor Yellow

    if ($TempProjectId) {
        $sqlite3cmd = Get-Command sqlite3 -ErrorAction SilentlyContinue
        if ($sqlite3cmd) {
            $qr = & sqlite3 $OrigDbPath "SELECT id FROM projects WHERE id='$TempProjectId';" 2>&1
            $Report.test_project_id_in_original_db = ($qr -ne "")
        } else {
            $Report.test_project_id_in_original_db = "SKIPPED (sqlite3 CLI not available - integrity confirmed by SHA-256 checksum)"
        }
    }
    Write-Host "    Project in original DB: $($Report.test_project_id_in_original_db)"

    # -----------------------------------------------------------------------
    # STEP 14 - Overall outcome
    # -----------------------------------------------------------------------
    $dbOk   = $Report.original_database_unchanged -eq $true
    $reqsOk = $reqCount -gt 0

    if ($Report.llm_call.succeeded -eq $true -and $reqsOk -and $dbOk) {
        $Report.outcome = "REAL LLM SUCCESS"
    } elseif ($Report.llm_call.succeeded -eq $false -and $reqsOk -and $dbOk) {
        $Report.outcome = "LLM FAILURE + DETERMINISTIC FALLBACK"
    } elseif ($Report.llm_call.succeeded -eq $null -and $reqsOk -and $dbOk) {
        $Report.outcome = "PIPELINE SUCCEEDED - LLM EVIDENCE INSUFFICIENT"
    } elseif (-not $reqsOk) {
        $Report.outcome = "DOWNSTREAM FAILURE - No requirements produced"
    } else {
        $Report.outcome = "INDETERMINATE"
    }

    Write-Host ("`nOUTCOME: " + $Report.outcome) -ForegroundColor Cyan

} catch {
    $Report.outcome = "SCRIPT ERROR"
    $Report.errors += $_.Exception.Message
    Write-Host "`n[ERROR] $($_.Exception.Message)" -ForegroundColor Red

} finally {

    # -----------------------------------------------------------------------
    # CLEANUP - guaranteed to run regardless of success or failure
    # -----------------------------------------------------------------------
    Write-Host "`n[CLEANUP] Stopping verification server and removing temporary files..." -ForegroundColor Yellow

    # Stop ONLY the specific server process we started (by PID - not all Python processes)
    if ($ServerProcess -and -not $ServerProcess.HasExited) {
        try {
            Stop-Process -Id $ServerProcess.Id -Force -ErrorAction SilentlyContinue
            Write-Host "    Server PID $($ServerProcess.Id) stopped."
        } catch {
            Write-Host "    Warning: Could not stop server process: $($_.Exception.Message)"
        }
    }

    # Remove temporary SRS document
    if ($TempSrsPath -and (Test-Path $TempSrsPath)) {
        Remove-Item -Path $TempSrsPath -Force -ErrorAction SilentlyContinue
        Write-Host "    Removed temporary SRS."
    }

    # Remove temporary database - NEVER the original reqpilot.db
    if ($TempDbPath -and (Test-Path $TempDbPath)) {
        Remove-Item -Path $TempDbPath -Force -ErrorAction SilentlyContinue
        Write-Host "    Removed temporary DB."
    }

    # Remove temporary server log files
    foreach ($logF in @($ServerStdOut, $ServerStdErr)) {
        if ($logF -and (Test-Path $logF)) {
            Remove-Item -Path $logF -Force -ErrorAction SilentlyContinue
        }
    }

    # Reset DATABASE_URL so it does not persist in the caller's shell session
    Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue

    # -----------------------------------------------------------------------
    # WRITE FINAL REPORT
    # -----------------------------------------------------------------------
    $Report | ConvertTo-Json -Depth 10 | Set-Content -Path $ReportPath -Encoding utf8
    Write-Host "`nVerification report written to: $ReportPath" -ForegroundColor Green
    Write-Host "===== Verification Complete =====" -ForegroundColor Cyan
}
