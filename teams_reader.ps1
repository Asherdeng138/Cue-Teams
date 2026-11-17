# Read Teams captions only. This file is bundled with the Teams edition.
# No audio capture, mouse input, keyboard input, scrolling or network calls.
param(
    [string]$OutPath,
    [string]$WindowTitle = 'Captions',
    [switch]$TeamsMode,
    [string]$PreferredWindow = '',
    [string[]]$TeamsProcess = @('ms-teams','Teams'),
    [switch]$LibraryOnly
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public static class CueTeamsWindows {
    public delegate bool Callback(IntPtr hwnd, IntPtr param);
    [DllImport("user32.dll")] static extern bool EnumWindows(Callback callback, IntPtr param);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hwnd);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr hwnd, StringBuilder s, int length);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
    public sealed class Win { public long Handle; public uint Pid; public string Title; }
    public static List<Win> List() {
        var result = new List<Win>();
        EnumWindows((h, p) => {
            if (!IsWindowVisible(h)) return true;
            var s = new StringBuilder(2048); GetWindowText(h,s,s.Capacity);
            if (s.Length == 0) return true;
            uint pid; GetWindowThreadProcessId(h,out pid);
            result.Add(new Win { Handle=h.ToInt64(), Pid=pid, Title=s.ToString() });
            return true;
        }, IntPtr.Zero);
        return result;
    }
}
'@

function Get-CueTree($Root) {
    # Read the Raw view: WebView caption containers need not be control elements.
    $nodes = [System.Collections.Generic.List[object]]::new()
    $stack = [System.Collections.Generic.Stack[object]]::new()
    $stack.Push(@{element=$Root; parent=-1; depth=0})
    $walker = [System.Windows.Automation.TreeWalker]::RawViewWalker
    $watch = [Diagnostics.Stopwatch]::StartNew()
    while ($stack.Count -gt 0 -and $nodes.Count -lt 7000 -and $watch.ElapsedMilliseconds -lt 9000) {
        $next = $stack.Pop(); $el = $next.element
        try {
            $current = $el.Current
            $role = $current.ControlType.ProgrammaticName.Replace('ControlType.','').ToLowerInvariant()
            $rid = ($el.GetRuntimeId() -join '-')
            $index = $nodes.Count
            $nodes.Add([pscustomobject]@{ index=$index; parent=$next.parent; depth=$next.depth;
                role=$role; name=[string]$current.Name; auto=[string]$current.AutomationId;
                class=[string]$current.ClassName; rid=$rid })
            if ($next.depth -ge 45) { continue }
            $kids = [System.Collections.Generic.List[object]]::new()
            $child = $walker.GetFirstChild($el)
            while ($null -ne $child -and $kids.Count -lt 1500) {
                $kids.Add($child); $child = $walker.GetNextSibling($child)
            }
            for ($i=$kids.Count-1; $i -ge 0; $i--) {
                $stack.Push(@{element=$kids[$i]; parent=$index; depth=$next.depth+1})
            }
        } catch { continue }
    }
    # Incomplete trees are never mistaken for a successful empty read.
    if ($stack.Count -gt 0) { throw 'Teams accessibility scan exceeded its limit. Keep the meeting window restored and retry.' }
    return ,$nodes.ToArray()
}

function Get-CueDescendants($Nodes, [int]$Index) {
    $depth = $Nodes[$Index].depth
    for ($i=$Index+1; $i -lt $Nodes.Count -and $Nodes[$i].depth -gt $depth; $i++) { $Nodes[$i] }
}

function Test-CueMetadata([string]$Text) {
    return $Text -match '^(?:\d{1,2}:\d{2}(?::\d{2})?|(?:已用时间|已用時間|Elapsed time|Duration)\s*\d.*)$'
}

function Get-CueCaptionEntries($Nodes) {
    # Region names alone are not enough: the "Turn on captions" button also matches.
    $hint = '(?i)caption|closed.?caption|字幕|转录|轉錄|文字记录|文字記錄'
    $regions = @($Nodes | Where-Object {
        $_.role -in @('pane','group','list','document','custom') -and
        (($_.auto + ' ' + $_.class) -match $hint -or ($_.name.Length -lt 60 -and $_.name -match $hint))
    })
    $best = @(); $bestDepth = -1
    foreach ($region in $regions) {
        $desc = @(Get-CueDescendants $Nodes $region.index)
        $texts = @($desc | Where-Object { $_.role -eq 'text' -and $_.name.Trim() -and -not (Test-CueMetadata $_.name.Trim()) })
        if ($texts.Count -eq 0) { continue }
        # Prefer the enclosing captions pane to an individual speaker-name span.
        if ($texts.Count -gt $best.Count -or ($texts.Count -eq $best.Count -and ($bestDepth -lt 0 -or $region.depth -lt $bestDepth))) {
            $best=$texts; $bestDepth=$region.depth; $scope=$region
        }
    }
    if ($best.Count -eq 0) { return @() }
    $scopeNodes = @($scope) + @(Get-CueDescendants $Nodes $scope.index)
    $used = @{}; $entries = [System.Collections.Generic.List[object]]::new()
    # Rows with an explicit speaker control win. The display name is retained verbatim.
    $speakers = @($scopeNodes | Where-Object {
        $_.name.Trim() -and ($_.auto + ' ' + $_.class) -match '(?i)speaker.?name|display.?name|author.?name|caption.?name|caption.?speaker|speaker.?display'
    })
    $speakerCandidates=$speakers
    $speakers=@($speakerCandidates | Where-Object {
        $childSpeakers=@(Get-CueDescendants $Nodes $_.index | Where-Object { $_.index -in $speakerCandidates.index })
        $childSpeakers.Count -eq 0
    })
    foreach ($sp in $speakers) {
        if ($sp.role -in @('button','image')) { continue }
        $parent = $sp.parent
        for ($level=0; $level -lt 4 -and $parent -ge $scope.index; $level++) {
            $desc = @(Get-CueDescendants $Nodes $parent)
            $otherSpeakers = @($desc | Where-Object { $_.index -ne $sp.index -and $_.index -in $speakers.index })
            if ($otherSpeakers.Count -gt 0) { break }
            $words = @($desc | Where-Object { $_.role -eq 'text' -and $_.index -ne $sp.index -and
                $_.name.Trim() -and $_.name -ne $sp.name -and -not (Test-CueMetadata $_.name.Trim()) -and
                $_.index -notin $speakers.index })
            if ($words.Count -gt 0) {
                $entries.Add([pscustomobject]@{id=$Nodes[$parent].rid; speaker=$sp.name.Trim(); text=(($words.name | ForEach-Object {$_.Trim()}) -join ' '); order=$words[0].index})
                foreach ($n in $desc) { $used[$n.index]=$true }
                break
            }
            $parent=$Nodes[$parent].parent
        }
    }
    # Other Teams layouts expose each caption as a row containing exactly two text
    # controls (name, words). Scope and row boundaries, not name capitalisation,
    # provide attribution. Never carry a name into a different row.
    foreach ($row in ($scopeNodes | Sort-Object depth -Descending)) {
        if ($row.role -notin @('listitem','group','custom','pane')) { continue }
        $desc = @(Get-CueDescendants $Nodes $row.index)
        $words = @($desc | Where-Object { $_.role -eq 'text' -and $_.name.Trim() -and -not (Test-CueMetadata $_.name.Trim()) })
        if ($words.Count -ne 2 -or $used.ContainsKey($words[0].index) -or $used.ContainsKey($words[1].index)) { continue }
        # A transcript pane with only two unrelated entries is not a caption row.
        if ($row.index -eq $scope.index) { continue }
        $entries.Add([pscustomobject]@{id=$row.rid; speaker=$words[0].name.Trim(); text=$words[1].name.Trim(); order=$words[0].index})
        $used[$words[0].index]=$true; $used[$words[1].index]=$true
    }
    # If Teams exposes words with semantic text IDs but withholds the name, keep
    # them and explicitly report an unknown speaker. Do not guess from avatar initials.
    foreach ($word in $best) {
        if (-not $used.ContainsKey($word.index) -and ($word.auto+' '+$word.class) -match '(?i)caption.?text|caption.?content|caption.?body|utterance.?text') {
            $entries.Add([pscustomobject]@{id=$word.rid; speaker=$null; text=$word.name.Trim(); order=$word.index})
        }
    }
    return @($entries | Sort-Object order | Select-Object id,speaker,text)
}

if ($LibraryOnly) { return }
try {
    $processIds = @()
    foreach ($name in $TeamsProcess) { $processIds += @([Diagnostics.Process]::GetProcessesByName($name) | ForEach-Object {$_.Id}) }
    $windows = @([CueTeamsWindows]::List() | Where-Object {
        ($_.Pid -in $processIds -or $_.Title -match '(?i)\|\s*Microsoft\s*Teams\s*$') -and
        $_.Title -notmatch '(?i)^(?:chat|聊天|日历|行事曆|calendar|activity|活动)\s*\|'
    })
    if ($PreferredWindow) { $windows=@($windows | Where-Object {$_.Title -eq $PreferredWindow}) }
    $chosen=$null; $entries=@()
    foreach ($window in $windows) {
        $root=[System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$window.Handle)
        $nodes=Get-CueTree $root
        # A live meeting has a leave/hang-up control. This excludes chats, recaps,
        # login screens and other Teams windows, even if their titles are similar.
        $live=@($nodes | Where-Object { $_.role -eq 'button' -and
            (($_.auto+' '+$_.class) -match '(?i)hangup|hang.up|leave.call|leave.meeting|call.end' -or
             $_.name -match '^(?:Leave|Hang up|离开|離開|挂断|掛斷)(?:\s|$)') })
        if ($live.Count -eq 0) { continue }
        $found=@(Get-CueCaptionEntries $nodes)
        if ($found.Count -gt 0) { $chosen=$window; $entries=$found; break }
    }
    if ($null -eq $chosen) {
        [Console]::Error.WriteLine('Waiting for Teams caption rows. Open live captions in the meeting; if captions are visible, this Teams layout may need adaptation. No text has been saved from this scan.')
        exit 2
    }
    $snapshot=@{schema='cue.teams.v1'; window_key=[string]$chosen.Handle; window=$chosen.Title; entries=@($entries)}
    $json=ConvertTo-Json -InputObject $snapshot -Depth 7 -Compress
    [IO.File]::WriteAllText($OutPath,$json,(New-Object Text.UTF8Encoding($false)))
    exit 0
} catch {
    [Console]::Error.WriteLine(('Teams caption reader: '+$_.Exception.Message))
    exit 1
}
