' User-facing launcher. Thin wrapper over start_ai_pos_silent.vbs
Option Explicit

Dim fso, sh, root, silent

Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")

root = fso.GetParentFolderName(WScript.ScriptFullName)
silent = root & "\start_ai_pos_silent.vbs"

If Not fso.FileExists(silent) Then
  MsgBox "start_ai_pos_silent.vbs not found." & vbCrLf & _
         "Run AI POS from the application folder.", _
         vbCritical, "AI POS"
  WScript.Quit 1
End If

' 0 = hide window; False = do not wait
sh.Run "wscript.exe """ & silent & """", 0, False
WScript.Quit 0
