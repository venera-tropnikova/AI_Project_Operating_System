' AI POS silent launcher (Windows)
' Hidden Local Bridge + browser. Portable root = folder of this .vbs.

Option Explicit

Dim fso, sh, root, bridge, url, pyCmd, launchCmd, portState

Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")

root = fso.GetParentFolderName(WScript.ScriptFullName)
bridge = root & "\tools\local_bridge.py"
url = "http://127.0.0.1:8080/"

If Not fso.FileExists(bridge) Then
  MsgBox "Не найден tools\local_bridge.py рядом с этим файлом." & vbCrLf & _
         "Запускайте AI POS из корня папки приложения.", _
         vbCritical, "AI POS"
  WScript.Quit 1
End If

portState = CheckPort8080()
If portState = "aipos" Then
  OpenBrowser url
  WScript.Quit 0
End If

If portState = "busy" Then
  MsgBox "Порт 8080 уже используется. Закройте другую программу или запустите AI POS на другом порту.", _
         vbExclamation, "AI POS"
  WScript.Quit 1
End If

' portState = "free"
pyCmd = FindPythonCommand()
If pyCmd = "" Then
  MsgBox "Для запуска AI POS установите Python 3", vbCritical, "AI POS"
  WScript.Quit 1
End If

launchCmd = pyCmd & " """ & bridge & """ --host 127.0.0.1 --port 8080"
' 0 = hide window; False = do not wait (bridge keeps running)
sh.Run launchCmd, 0, False

WScript.Sleep 1000
OpenBrowser url
WScript.Quit 0

Sub OpenBrowser(targetUrl)
  Dim browserCmd
  browserCmd = "cmd /c start """" """ & targetUrl & """"
  sh.Run browserCmd, 0, False
End Sub

Function CheckPort8080()
  ' Returns: "free" | "aipos" | "busy"
  Dim http, errNum, body, statusCode

  On Error Resume Next
  Err.Clear
  Set http = CreateObject("WinHttp.WinHttpRequest.5.1")
  If Err.Number <> 0 Or http Is Nothing Then
    Err.Clear
    Set http = CreateObject("MSXML2.XMLHTTP")
  End If
  If Err.Number <> 0 Or http Is Nothing Then
    CheckPort8080 = "free"
    Exit Function
  End If

  Err.Clear
  On Error Resume Next
  http.SetTimeouts 500, 500, 1000, 1500
  Err.Clear
  http.Open "GET", "http://127.0.0.1:8080/api/health", False
  http.Send
  errNum = Err.Number
  If errNum <> 0 Then
    Err.Clear
    http.Open "GET", "http://127.0.0.1:8080/", False
    http.Send
    errNum = Err.Number
    If errNum <> 0 Then
      CheckPort8080 = "free"
      Exit Function
    End If
    statusCode = http.Status
    body = "" & http.responseText
    If LooksLikeAiPos(body) Then
      CheckPort8080 = "aipos"
    Else
      CheckPort8080 = "busy"
    End If
    Exit Function
  End If

  statusCode = http.Status
  body = "" & http.responseText
  If statusCode >= 200 And statusCode < 500 Then
    If LooksLikeAiPos(body) Then
      CheckPort8080 = "aipos"
    Else
      CheckPort8080 = "busy"
    End If
  Else
    CheckPort8080 = "busy"
  End If
End Function

Function LooksLikeAiPos(body)
  Dim text
  text = LCase("" & body)
  If InStr(text, "ai-pos-local-bridge") > 0 Then
    LooksLikeAiPos = True
    Exit Function
  End If
  If InStr(text, "ai pos") > 0 And InStr(text, "<!doctype html") > 0 Then
    LooksLikeAiPos = True
    Exit Function
  End If
  If InStr(text, "ai project operating system") > 0 Then
    LooksLikeAiPos = True
    Exit Function
  End If
  LooksLikeAiPos = False
End Function

Function FindPythonCommand()
  Dim candidates, i, probe, exitCode
  ' Spec order: pythonw.exe, then py -3, then python
  candidates = Array( _
    "pythonw.exe", _
    "py -3", _
    "python" _
  )
  For i = 0 To UBound(candidates)
    probe = "cmd /c " & candidates(i) & " --version >nul 2>nul"
    exitCode = sh.Run(probe, 0, True)
    If exitCode = 0 Then
      FindPythonCommand = candidates(i)
      Exit Function
    End If
  Next
  FindPythonCommand = ""
End Function
