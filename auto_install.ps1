$FolderName = $HOME + "\Documents\mangrove-data-management-master"
if (Test-Path $FolderName) {
   Remove-Item -LiteralPath $FolderName -Force -Recurse
}
#PowerShell Create directory if not exists
#New-Item $FolderName -ItemType Directory

$File = $(New-TemporaryFile ).FullName + ".zip"
Invoke-WebRequest -Uri "https://github.com/UCSD-E4E/mangrove-data-management/archive/refs/heads/master.zip" -OutFile $File
Expand-Archive -Path $File -Destination $HOME\Documents
Set-Location $FolderName
python3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --upgrade .
explorer .venv\Scripts
