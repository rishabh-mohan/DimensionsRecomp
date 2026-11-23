Add-Type -Name G -Namespace W -MemberDefinition '[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern void DisableProcessWindowsGhosting();'
[W.G]::DisableProcessWindowsGhosting()
Add-Type -AssemblyName System.Windows.Forms
$f = New-Object System.Windows.Forms.Form
$f.Text = 'testg-standin-hung'
$f.Show()
[System.Windows.Forms.Application]::DoEvents()
[System.Threading.Thread]::Sleep(600000)