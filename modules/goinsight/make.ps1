#Requires -Version 5.1
<#
.SYNOPSIS
  PowerShell equivalent of Makefile tasks for Windows users.

.DESCRIPTION
  Usage examples:
    ./make.ps1 help
    ./make.ps1 setup
    ./make.ps1 docs
    ./make.ps1 tests
    ./make.ps1 get-model
    ./make.ps1 opt-model
    ./make.ps1 run-model
    ./make.ps1 clean
#>

param(
  [Parameter(Position=0)]
  [ValidateSet("help", "setup", "clean", "docs", "tests", "get-model", "opt-model", "run-model")]
  [string]$Target = "help"
)

# --- Hardening / strictness ---
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# --- Configuration ---
$VENV = ".venv"
# Prefer Python launcher if available, else fallback to python
$PY_CMD = if (Get-Command py -ErrorAction SilentlyContinue) { 'py -3' } else { 'python' }

$SOURCEDIR = "docs"
$BUILDDIR  = "docs/_build"
$HTMLDIR   = Join-Path $BUILDDIR "html"
$INDEXFILE = Join-Path $HTMLDIR "index.html"

# KataGo (Windows)
$MODEL_DIR   = "model"
$MODEL_ZIP   = Join-Path $MODEL_DIR "katago.zip"
# Windows CPU-only (Eigen) build; for GPU swap to an OpenCL/CUDA/TensorRT Windows zip from releases
$MODEL_URL   = "https://github.com/lightvector/KataGo/releases/download/v1.16.3/katago-v1.16.3-eigen-windows-x64.zip"
$NEURALNET_DIR  = "neuralnet"
$NEURALNET_FILE = Join-Path $NEURALNET_DIR "g170e-b10c128-s1141046784-d204142634.bin.gz"
$NEURALNET_URL = "https://katagoarchive.org/g170/neuralnets/g170e-b10c128-s1141046784-d204142634.bin.gz"
$CONFIG_FILE    = Join-Path $MODEL_DIR "default_gtp.cfg"
$BENCHMARK_OUT  = Join-Path $MODEL_DIR "benchmark_output.txt"

# --- Helper Functions (venv/docs/tests) ---

function Create-Venv {
  Write-Host "`nChecking Python installation..."
  try { 
      $pyVersionOutput = & $PY_CMD --version 2>&1
      $pyVersionOutput = $pyVersionOutput -replace '[^\d\.]', ''
  } catch {
      Write-Error "Python not found. Please install Python 3.7 or higher and ensure it's on PATH."
      exit 1
  }

  # Parse version numbers
  $versionParts = $pyVersionOutput.Split('.')
  $major = [int]$versionParts[0]
  $minor = [int]$versionParts[1]

  if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 7)) {
      Write-Error "Python 3.7 or higher is required. Found $pyVersionOutput. Please upgrade Python."
      exit 1
  }

  Write-Host "Python version $pyVersionOutput detected."

  if (-not (Test-Path $VENV)) {
    Write-Host "`nCreating virtual environment in $VENV..."
    iex "$PY_CMD -m venv $VENV"
  } else { Write-Host "`nVirtual environment already exists." }

  $pip = Join-Path $VENV "Scripts\pip.exe"
  if (-not (Test-Path $pip)) { Write-Error "pip not found. venv creation failed."; exit 1 }

  Write-Host "`nUpgrading pip..."
  & $pip install --upgrade pip | Out-Host

  if (Test-Path "requirements.txt") {
    Write-Host "`nInstalling dependencies from requirements.txt..."
    & $pip install -r requirements.txt
  } else {
    Write-Warning "requirements.txt not found. Skipping dependency installation."
  }
}

function Ensure-Sphinx {
  $sphinx = Join-Path $VENV "Scripts\sphinx-build.exe"
  if (Test-Path $sphinx) { return $sphinx }
  $pip = Join-Path $VENV "Scripts\pip.exe"
  Write-Warning "Sphinx not found in venv. Installing 'sphinx'..."
  & $pip install sphinx | Out-Host
  if (-not (Test-Path $sphinx)) { throw "sphinx-build still missing after install." }
  return $sphinx
}

function Build-Docs {
  Write-Host "`nBuilding documentation..."
  if (-not (Test-Path $VENV)) { throw "Virtual environment not found. Run './make.ps1 setup' first." }
  New-Item -ItemType Directory -Force -Path $HTMLDIR | Out-Null
  $sphinx = Ensure-Sphinx
  & $sphinx -b html $SOURCEDIR $HTMLDIR
  Write-Host "Docs built at $INDEXFILE"
}

function Open-Docs {
  if (-not (Test-Path $INDEXFILE)) {
    Write-Warning "Documentation not found. Building docs first..."
    Build-Docs
  }
  Write-Host "Opening documentation..."
  Start-Process $INDEXFILE
}

function Clean {
  Write-Host "`nRemoving virtual environment, build dir, models, logs..."
  foreach ($p in @($VENV, $BUILDDIR, $MODEL_DIR, $NEURALNET_DIR, "gtp_logs")) {
    if (Test-Path $p) {
      try { Remove-Item -Recurse -Force $p } catch { Write-Warning "Could not remove ${p}: $($_.Exception.Message)" }
    }
  }
  Write-Host "Cleanup complete."
}

function Ensure-Pytest {
  $pythonExe = Join-Path $VENV "Scripts\python.exe"
  if (-not (Test-Path $pythonExe)) { throw "Python in venv not found. Run './make.ps1 setup' first." }
  try { & $pythonExe -m pytest --version | Out-Null } catch {
    Write-Warning "pytest not found in venv. Installing 'pytest'..."
    & (Join-Path $VENV "Scripts\pip.exe") install pytest | Out-Host
  }
  return $pythonExe
}

function Run-Tests {
  Write-Host "Running Python tests..." -ForegroundColor Cyan
  $pythonExe = Ensure-Pytest
  & $pythonExe -m pytest -v
}

# --- KataGo helpers (model/benchmark/run) ---

function Resolve-KataGoExe {
  $exe = Get-ChildItem -Path $MODEL_DIR -Recurse -Filter 'katago.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $exe) { throw "katago.exe not found under '$MODEL_DIR'. Did extraction succeed?" }
  return $exe.FullName
}

function Get-Model {
  New-Item -ItemType Directory -Force -Path $MODEL_DIR,$NEURALNET_DIR | Out-Null

  Write-Host "Downloading KataGo (Windows, CPU/Eigen build)..."
  Invoke-WebRequest -Uri $MODEL_URL -OutFile $MODEL_ZIP

  Write-Host "Extracting KataGo zip..."
  if (-not (Get-ChildItem -Path $MODEL_DIR -Recurse -Filter 'katago.exe' -ErrorAction SilentlyContinue)) {
    Expand-Archive -Path $MODEL_ZIP -DestinationPath $MODEL_DIR -Force
  } else { Write-Host "KataGo already extracted." }

  Write-Host "Downloading neural network (.bin.gz)..."
  Invoke-WebRequest -Uri $NEURALNET_URL -OutFile $NEURALNET_FILE

  Write-Host "Model ready!"
}

function Run-Benchmark {
  $katago = Resolve-KataGoExe
  if (-not (Test-Path $NEURALNET_FILE)) { throw "Neural net not found at $NEURALNET_FILE. Run './make.ps1 get-model' first." }
  if (-not (Test-Path $CONFIG_FILE))   { throw "Config file not found at $CONFIG_FILE." }

  Write-Host "Starting benchmark procedure, this will take a while... (Ctrl + C to cancel)"
  Start-Sleep -Seconds 5
  & $katago benchmark -model $NEURALNET_FILE -config $CONFIG_FILE 2>&1 | Tee-Object -FilePath $BENCHMARK_OUT
  Write-Host "Benchmark done."
}

function Apply-OptimalThreads {
  if (-not (Test-Path $BENCHMARK_OUT)) { throw "Benchmark output not found at $BENCHMARK_OUT" }

  # Find a line that contains "(recommended)" and capture numSearchThreads = N
  $line = Select-String -Path $BENCHMARK_OUT -Pattern '\bnumSearchThreads\s*=\s*\d+.*\(recommended\)' | Select-Object -First 1
  if (-not $line) { throw "Could not find a '(recommended)' numSearchThreads in benchmark output." }

  $recommended = [int]([regex]::Match($line.Line, 'numSearchThreads\s*=\s*(\d+)').Groups[1].Value)
  if (-not $recommended) { throw "Failed to parse recommended numSearchThreads." }

  if (-not (Test-Path $CONFIG_FILE)) { throw "Config file not found at $CONFIG_FILE" }

  # Replace existing line or append if not present
  $cfg = Get-Content $CONFIG_FILE -ErrorAction Stop
  if ($cfg -match '^\s*numSearchThreads\s*=') {
    $cfg = $cfg -replace '^\s*numSearchThreads\s*=\s*\d+', "numSearchThreads = $recommended"
  } else {
    $cfg += "numSearchThreads = $recommended"
  }
  $cfg | Set-Content -Encoding ASCII $CONFIG_FILE

  Write-Host "Changed number of search threads to $recommended, optimisation done!"
}

function Start-GTP {
  $katago = Resolve-KataGoExe
  if (-not (Test-Path $NEURALNET_FILE)) { throw "Neural net not found at $NEURALNET_FILE. Run './make.ps1 get-model' first." }
  if (-not (Test-Path $CONFIG_FILE))   { throw "Config file not found at $CONFIG_FILE." }

  Write-Host "Starting KataGo..."
  & $katago gtp -model $NEURALNET_FILE -config $CONFIG_FILE
}

# --- Help ---

function Show-Help {
  Write-Host "Available commands:" -ForegroundColor Cyan
  Write-Host "  ./make.ps1 setup      - Create venv, install deps, build docs"
  Write-Host "  ./make.ps1 docs       - Build (if needed) and open docs"
  Write-Host "  ./make.ps1 tests      - Run Python tests (auto-installs pytest if missing)"
  Write-Host "  ./make.ps1 get-model  - Download KataGo (Windows build) + neural net"
  Write-Host "  ./make.ps1 opt-model  - Benchmark then set recommended numSearchThreads in cfg"
  Write-Host "  ./make.ps1 run-model  - Start a GTP session with the model"
  Write-Host "  ./make.ps1 clean      - Remove venv, docs, model, neuralnet and logs"
  Write-Host ""
  Write-Host "Activate the venv (PowerShell):" -ForegroundColor DarkGray
  Write-Host "  .\$VENV\Scripts\Activate.ps1" -ForegroundColor DarkGray
}

# --- Main dispatcher ---
switch ($Target) {
  "help"      { Show-Help }
  "setup"     { Create-Venv; Build-Docs; Write-Host "`nSetup complete!" -ForegroundColor Green; Write-Host "######################################"; Write-Host "# To activate your virtual env:"; Write-Host "#   .\$VENV\Scripts\Activate.ps1"; Write-Host "######################################" }
  "docs"      { Open-Docs }
  "tests"     { Run-Tests }
  "get-model" { Get-Model }
  "opt-model" { Run-Benchmark; Apply-OptimalThreads }
  "run-model" { Start-GTP }
  "clean"     { Clean }
}
