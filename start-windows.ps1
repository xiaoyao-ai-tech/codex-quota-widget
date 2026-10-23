param([switch]$Demo)
$ErrorActionPreference = 'Stop'
$python = (Get-Command python -ErrorAction Stop).Source
& $python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'
if ($LASTEXITCODE -ne 0) {
    throw 'Python 3.12+ is required.'
}
& $python -c 'import PySide6.QtWidgets' 2>$null
if ($LASTEXITCODE -ne 0) {
    throw 'Install the Windows UI dependency first: python -m pip install -r requirements-windows.txt'
}
$pythonw = Join-Path (Split-Path $python) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonw)) {
    throw 'pythonw.exe is required (Python 3.12+ from python.org).'
}
$arguments = '"' + (Join-Path $PSScriptRoot 'windows_widget.py') + '"'
if ($Demo) { $arguments += ' --demo' }
Start-Process -FilePath $pythonw -ArgumentList $arguments -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
