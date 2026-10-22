# build-alula.ps1 - builds the program `alula`: target/alula.exe from src/alula.nv, and prints the path of the file.
#
#   powershell -File scripts/build-alula.ps1             build
#   powershell -File scripts/build-alula.ps1 -Test       build, then run the program on the machines of src/machine (`alula test`)
#
# It needs Nova Oracle 0.1.0 and Clang (spikes/env/README.md, part 1): the environment of Nova is set up by its `setup-env.ps1` (NOVA_STD_PATH is set),
# run it with a leading dot in the same console before this script. The script installs nothing and does not change PATH or any setting of the machine:
# the program is one file in target/ (it is not committed; .gitignore).
param(
    [switch]$Test
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root

if (-not (Get-Command nova -ErrorAction SilentlyContinue)) {
    Write-Error "nova is not on PATH: run the setup-env.ps1 of Nova Oracle 0.1.0 first (leading dot), see spikes/env/README.md"
    exit 2
}

$exe = Join-Path $root 'target/alula.exe'
& nova build src/alula.nv -o $exe
if ($LASTEXITCODE -ne 0) { Write-Error "nova build failed"; exit $LASTEXITCODE }
if (-not (Test-Path -LiteralPath $exe)) { Write-Error "the build did not leave $exe"; exit 1 }

if ($Test) {
    & $exe test (Join-Path $root 'src/machine')
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Output $exe
