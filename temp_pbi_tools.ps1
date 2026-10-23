# Temporary helper for checking the generated report in Power BI Desktop.
#   -Action shot  -Out <png>      capture the Desktop window (PrintWindow, no focus change)
#   -Action click -Name <text>    invoke a button / select a tab whose name matches
#   -Action list                  list visible named controls (debug)
param([string]$Action = "shot", [string]$Out = "$env:TEMP\tashots\pbi.png", [string]$Name = "")
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Drawing;
public class PW {
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint f);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  public struct RECT { public int L, T, R, B; }
  public static void Shot(IntPtr h, string path) { RECT r; GetWindowRect(h, out r); int w = r.R - r.L, ht = r.B - r.T; var b = new Bitmap(w, ht); using (var g = Graphics.FromImage(b)) { var dc = g.GetHdc(); PrintWindow(h, dc, 2); g.ReleaseHdc(dc); } b.Save(path); }
}
"@ -ReferencedAssemblies System.Drawing
[PW]::SetProcessDPIAware() | Out-Null
$procs = Get-Process PBIDesktop -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 }
if (-not $procs) { "no PBIDesktop window"; exit 1 }
$p = $procs | Select-Object -First 1
if ($Action -eq "shot") {
  New-Item -ItemType Directory -Force (Split-Path $Out) | Out-Null
  [PW]::Shot($p.MainWindowHandle, $Out); "saved $Out ($($p.MainWindowTitle))"; exit 0
}
$root = [System.Windows.Automation.AutomationElement]::FromHandle($p.MainWindowHandle)
$all = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
if ($Action -eq "list") {
  foreach ($e in $all) { $n = $e.Current.Name; if ($n -and $n.Length -lt 120) { "$($e.Current.ControlType.ProgrammaticName) | $n | $($e.Current.AutomationId)" } }
  exit 0
}
foreach ($e in $all) {
  $n = $e.Current.Name
  if ($n -eq $Name -or $n -like "$Name,*" -or $n -like "$Name *") {
    $ct = $e.Current.ControlType
    try {
      if ($ct -eq [System.Windows.Automation.ControlType]::TabItem) { $e.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select() }
      elseif ($ct -eq [System.Windows.Automation.ControlType]::ListItem) { $e.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select() }
      else { $e.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke() }
      "clicked $n ($($ct.ProgrammaticName))"; exit 0
    } catch { }
  }
}
"not found: $Name"; exit 1
