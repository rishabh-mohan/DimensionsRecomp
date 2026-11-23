<#
.SYNOPSIS
  compile-one: compile ONE translation unit with the exact flags from a compile_commands.json,
  writing the object (and dep file) into -OutDir instead of the build tree.

.DESCRIPTION
  Looks up <Source> in the compile database (default: build\sdk-dev\compile_commands.json = dev SDK,
  -Db overrides, e.g. build\dev\compile_commands.json = dev game tree), picks the entry for -Config
  (default Release: object path under \Release\, else -O3), rewrites -o / -MF / -MT into -OutDir and runs
  the compiler in the entry's directory. Nothing in the build tree is written or linked, so it is safe
  to run while other builds are going.

  <Source> may be absolute, relative to the current directory, relative to the workspace root, or any
  unique path suffix in the database (e.g. src\core\clock.cpp).
  -SyntaxOnly   replace "-c ... -o ..." and the dep-file flags with -fsyntax-only (nothing is written).
  -Config       Debug / Release / RelWithDebInfo for multi-config databases (default Release).
  -Target       substring of the object path to pick one entry when a file is compiled by several targets.
  Extra compiler flags: append them at the end (e.g. -ftime-trace -H -Wno-foo); they are passed through
  verbatim. Flags that PowerShell would read as one of this script's parameters (-E, -P, -T, -c, -S, ...)
  must be given as -Extra:'-E' (or -Extra '-E' when calling from PowerShell with &).
  -PrintOnly    print the rewritten command and the working directory, do not compile.
  If the target's precompiled header (.pch) has not been built, the -include-pch flags are dropped and the
  PCH header is included as plain source (same semantics, slower).
  Exit code = compiler exit code (2 = lookup error). Written for Windows PowerShell 5.1.

.EXAMPLE
  powershell -NoProfile -File env\compile-one.ps1 DimensionsRecomp\rexglue-sdk\src\core\clock.cpp -OutDir build\agent5\obj
.EXAMPLE
  powershell -NoProfile -File env\compile-one.ps1 DimensionsRecomp\rexlego\src\main.cpp -OutDir build\agent5\obj -Db build\dev\compile_commands.json -SyntaxOnly
#>
# Deliberately NOT an advanced script ([CmdletBinding()]/[Parameter()]): the common parameter -Debug has the
# alias -db, which would clash with -Db. Unbound arguments ($args) are extra compiler flags.
param(
    [string]$Source,
    [string]$OutDir,
    [switch]$SyntaxOnly,
    [string]$Db,
    [string]$Config = 'Release',
    [string]$Target,
    [string[]]$Extra = @(),
    [switch]$PrintOnly
)
$ErrorActionPreference = 'Stop'
$Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$Cwd = (Get-Location).ProviderPath
$Extra = @($Extra) + @($args | ForEach-Object { [string]$_ })

function Fail([string]$msg, [int]$code = 2) { [Console]::Error.WriteLine("compile-one: $msg"); exit $code }
if (-not $Source -or -not $OutDir) {
    Fail 'usage: compile-one.ps1 <source> -OutDir <dir> [-SyntaxOnly] [-Db <compile_commands.json>] [-Config Release] [-Target <obj-path-substring>] [-PrintOnly] [extra compiler flags...]'
}
function NormPath([string]$p) {
    $p = $p.Replace('\', '/')
    if ($p -match '/\.\.?/') { $p = [IO.Path]::GetFullPath($p).Replace('\', '/') }
    return $p.ToLowerInvariant()
}
function Resolve-UserPath([string]$p) {
    if ([IO.Path]::IsPathRooted($p)) { return [IO.Path]::GetFullPath($p) }
    foreach ($base in @($Cwd, $Root)) {
        $c = [IO.Path]::GetFullPath([IO.Path]::Combine($base, $p))
        if (Test-Path -LiteralPath $c) { return $c }
    }
    return $null
}
# Split a Windows command line into RAW tokens (quotes kept) so tokens can be rewritten and re-joined verbatim.
function Split-Raw([string]$s) {
    $tokens = New-Object System.Collections.Generic.List[string]
    $sb = New-Object System.Text.StringBuilder
    $inQ = $false; $bs = 0
    foreach ($ch in $s.ToCharArray()) {
        if ($ch -eq [char]'\') { $bs++; [void]$sb.Append($ch); continue }
        if ($ch -eq [char]'"') { if (($bs % 2) -eq 0) { $inQ = -not $inQ }; $bs = 0; [void]$sb.Append($ch); continue }
        $bs = 0
        if (-not $inQ -and ($ch -eq [char]' ' -or $ch -eq [char]"`t")) {
            if ($sb.Length -gt 0) { $tokens.Add($sb.ToString()); [void]$sb.Clear() }
            continue
        }
        [void]$sb.Append($ch)
    }
    if ($sb.Length -gt 0) { $tokens.Add($sb.ToString()) }
    return , $tokens
}
function Quote([string]$a) {
    if ($a -eq '') { return '""' }
    if ($a -notmatch '[\s"]') { return $a }
    $a = $a -replace '(\\*)"', '$1$1\"'
    $a = $a -replace '(\\+)$', '$1$1'
    return '"' + $a + '"'
}
function Get-Command-String($e) {
    if ($e.ContainsKey('command')) { return [string]$e['command'] }
    return ((@($e['arguments']) | ForEach-Object { Quote ([string]$_) }) -join ' ')
}
function Get-ObjArg($tok) {
    for ($i = 1; $i -lt $tok.Count; $i++) {
        if ($tok[$i] -ceq '-o' -and $i + 1 -lt $tok.Count) { return $tok[$i + 1].Trim('"') }
        if ($tok[$i] -cmatch '^[-/]Fo(.+)$') { return $Matches[1].Trim('"') }
    }
    return $null
}

# ---- compile database -------------------------------------------------------------------------------
if (-not $Db) { $Db = Join-Path $Root 'build\sdk-dev\compile_commands.json' }
$dbPath = Resolve-UserPath $Db
if (-not $dbPath) { Fail "compile database not found: $Db" }
Add-Type -AssemblyName System.Web.Extensions
$ser = New-Object System.Web.Script.Serialization.JavaScriptSerializer
$ser.MaxJsonLength = [int]::MaxValue
$entries = $ser.DeserializeObject([IO.File]::ReadAllText($dbPath))

$srcFull = Resolve-UserPath $Source
$want = $null; if ($srcFull) { $want = NormPath $srcFull }
$rel = $Source.Replace('\', '/'); while ($rel.StartsWith('./')) { $rel = $rel.Substring(2) }
$suffix = '/' + $rel.ToLowerInvariant()
$exact = New-Object System.Collections.Generic.List[object]
$bySuffix = New-Object System.Collections.Generic.List[object]
foreach ($e in $entries) {
    $f = [string]$e['file']
    if (-not [IO.Path]::IsPathRooted($f)) { $f = [IO.Path]::Combine([string]$e['directory'], $f) }
    $nf = NormPath $f
    $e['_nf'] = $nf
    if ($want -and $nf -eq $want) { $exact.Add($e) } elseif ($nf.EndsWith($suffix)) { $bySuffix.Add($e) }
}
$cands = $exact; if ($cands.Count -eq 0) { $cands = $bySuffix }
$files = @($cands | ForEach-Object { $_['_nf'] } | Sort-Object -Unique)
if ($files.Count -eq 0) { Fail "no entry for '$Source' in $dbPath" }
if ($files.Count -gt 1) { Fail ("'$Source' matches several files in ${dbPath}:`n  " + ($files -join "`n  ")) }

# ---- pick the entry for -Config (and -Target) -------------------------------------------------------------
$cfgRe = '[\\/]' + [regex]::Escape($Config) + '[\\/]'
$info = foreach ($e in $cands) {
    $cmd = Get-Command-String $e
    $tok = Split-Raw $cmd
    $o = [string]$e['output']; if (-not $o) { $o = Get-ObjArg $tok }
    [pscustomobject]@{ E = $e; Cmd = $cmd; Tok = $tok; Obj = [string]$o }
}
if ($Target) { $info = @($info | Where-Object { $_.Obj -like "*$Target*" }); if (-not $info) { Fail "no entry for '$Source' with -Target '$Target'" } }
$multi = @($info | Where-Object { $_.Obj -match '[\\/](Debug|Release|RelWithDebInfo|MinSizeRel)[\\/]' }).Count -gt 0
$sel = @($info | Where-Object { $_.Obj -match $cfgRe })
if ($sel.Count -eq 0 -and -not $multi) {
    $sel = @($info)    # single-config database
    if ($Config -eq 'Release' -and $sel.Count -gt 1) { $o3 = @($sel | Where-Object { $_.Cmd -match '(^|\s)-O3(\s|$)' }); if ($o3) { $sel = $o3 } }
}
if ($sel.Count -eq 0) { Fail ("no $Config entry for '$Source'. Objects:`n  " + (($info | ForEach-Object Obj) -join "`n  ")) }
if ($sel.Count -gt 1) {
    [Console]::Error.WriteLine("compile-one: $($sel.Count) $Config entries (use -Target to choose); using the first:`n  " + (($sel | ForEach-Object Obj) -join "`n  "))
}
$pick = $sel[0]
$dir = [string]$pick.E['directory']
$tok = $pick.Tok
$file = [string]$pick.E['file']

# ---- rewrite -----------------------------------------------------------------------------------------
$outFull = [IO.Path]::GetFullPath([IO.Path]::Combine($Cwd, $OutDir))
$origObj = Get-ObjArg $tok
if ($origObj) { $leaf = [IO.Path]::GetFileName($origObj) } else { $leaf = [IO.Path]::GetFileName($file) + '.obj' }
$obj = Join-Path $outFull $leaf
$dep = $obj + '.d'
$exe = $tok[0].Trim('"')
$out = New-Object System.Collections.Generic.List[string]
$sawO = $false; $notes = @()
for ($i = 1; $i -lt $tok.Count; $i++) {
    $t = $tok[$i]
    $next = $null; if ($i + 1 -lt $tok.Count) { $next = $tok[$i + 1] }
    if ($t -ceq '-o') { $i++; $sawO = $true; if (-not $SyntaxOnly) { $out.Add('-o'); $out.Add((Quote $obj)) }; continue }
    if ($t -cmatch '^[-/]Fo') { $sawO = $true; if (-not $SyntaxOnly) { $out.Add((Quote ($t.Substring(0, 3) + $obj))) }; continue }
    if ($t -ceq '-c') { if (-not $SyntaxOnly) { $out.Add('-c') }; continue }
    if ($t -ceq '-MF') { $i++; if (-not $SyntaxOnly) { $out.Add('-MF'); $out.Add((Quote $dep)) }; continue }
    if ($t -ceq '-MT' -or $t -ceq '-MQ') { $i++; if (-not $SyntaxOnly) { $out.Add($t); $out.Add((Quote $obj)) }; continue }
    if ($t -ceq '-MD' -or $t -ceq '-MMD') { if (-not $SyntaxOnly) { $out.Add($t) }; continue }
    # precompiled header that has not been built yet: drop it (the PCH header stays force-included as source)
    $pchArg = $null; $span = 0
    if ($t -ceq '-Xclang' -and $next -ceq '-include-pch' -and $i + 3 -lt $tok.Count -and $tok[$i + 2] -ceq '-Xclang') { $pchArg = $tok[$i + 3]; $span = 3 }
    elseif ($t -ceq '-include-pch' -and $next) { $pchArg = $next; $span = 1 }
    if ($pchArg) {
        $pch = [IO.Path]::Combine($dir, $pchArg.Trim('"'))
        if (-not (Test-Path -LiteralPath $pch)) { $i += $span; $notes += "PCH not built ($pch): compiling with the PCH header as plain source"; continue }
    }
    $out.Add($t)
}
if (-not $SyntaxOnly -and -not $sawO) { $out.Add('-o'); $out.Add((Quote $obj)) }
if ($SyntaxOnly) { $out.Add('-fsyntax-only') }
foreach ($x in $Extra) { if ($x) { $out.Add($x) } }
$argStr = $out -join ' '

if ($PrintOnly) {
    "cd $dir"
    (Quote $exe) + ' ' + $argStr
    foreach ($n in $notes) { "note: $n" }
    exit 0
}

# ---- environment + run -------------------------------------------------------------------------------
if (-not $env:LEGO_LLVM -or -not $env:INCLUDE) { . (Join-Path $Root 'env\devshell.ps1') 6>$null | Out-Null }
if (-not $SyntaxOnly) { New-Item -ItemType Directory -Force -Path $outFull | Out-Null }
foreach ($n in $notes) { [Console]::Error.WriteLine("compile-one: note: $n") }
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $exe
$psi.Arguments = $argStr
$psi.WorkingDirectory = $dir
$psi.UseShellExecute = $false
$sw = [Diagnostics.Stopwatch]::StartNew()
$p = [System.Diagnostics.Process]::Start($psi)
$p.WaitForExit()
$code = $p.ExitCode
$secs = [Math]::Round($sw.Elapsed.TotalSeconds, 2)
if ($SyntaxOnly) { $what = 'syntax-only' } else { $what = "-> $obj" }
Write-Host "compile-one: $Config $([IO.Path]::GetFileName($file)) $what exit=$code ${secs}s"
exit $code
