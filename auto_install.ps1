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
if (Get-Command $cmdName -errorAction SilentlyContinue)
{
    "$cmdName exists"
}
else
{
	$File = $(New-TemporaryFile ).FullName + ".exe"
	Invoke-WebRequest -Uri "https://download.visualstudio.microsoft.com/download/pr/1eb43f77-61af-40b0-8a5a-6165724dca60/f12aac6d4a907b4d54f5d41317aae0f7/dotnet-sdk-6.0.201-win-x64.exe" -OutFile $File
	$File
	dotnet tool install --global Clcrutch.Caffeinate --version 0.1.4-alpha

}