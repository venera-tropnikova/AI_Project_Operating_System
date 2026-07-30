' AI POS silent launcher (Windows)
' Hidden Local Bridge + browser. Portable root = folder of this .vbs.

Option Explicit

Dim fso, sh, root, bridge, url, pyCmd, launchCmd, portState
Dim WAIT_MS, POLL_MS

WAIT_MS = 20000
POLL_MS = 500

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

' Already healthy AI POS on 8080: open browser only, do not start a second server.
If HealthReady() Then
  OpenBrowser url
  WScript.Quit 0
End If

portState = CheckPort8080()
If portState = "aipos" Then
  ' HealthReady failed but body looked like AI POS — still open only.
  OpenBrowser url
  WScript.Quit 0
End If

If portState = "busy" Then
  MsgBox "Порт 8080 уже используется другой программой." & vbCrLf & _
         "Закройте её или освободите порт, затем запустите AI POS снова.", _
         vbExclamation, "AI POS"
  WScript.Quit 1
End If

' portState = "free"
pyCmd = FindPythonCommand()
If pyCmd = "" Then
  MsgBox "Для запуска AI POS установите Python 3." & vbCrLf & _
         "Нужны команды: py -3 или python.", _
         vbCritical, "AI POS"
  WScript.Quit 1
End If

launchCmd = pyCmd & " """ & bridge & """ --host 127.0.0.1 --port 8080"
' 0 = hide window; False = do not wait (bridge keeps running)
sh.Run launchCmd, 0, False

If Not WaitForHealth(WAIT_MS, POLL_MS) Then
  MsgBox "Не удалось запустить AI POS." & vbCrLf & vbCrLf & _
         "Local Bridge не ответил на http://127.0.0.1:8080/api/health за " & _
         CStr(WAIT_MS \ 1000) & " с." & vbCrLf & vbCrLf & _
         "Интерпретатор: " & pyCmd & vbCrLf & _
         "Проверьте Python 3 и что порт 8080 свободен." & vbCrLf & _
         "Браузер не открыт, чтобы не показать пустую страницу.", _
         vbCritical, "AI POS"
  WScript.Quit 1
End If

OpenBrowser url
WScript.Quit 0

Sub OpenBrowser(targetUrl)
  Dim browserCmd
  browserCmd = "cmd /c start """" """ & targetUrl & """"
  sh.Run browserCmd, 0, False
End Sub

Function HealthReady()
  ' True only when /api/health returns OK and looks like AI POS Local Bridge.
  Dim http, errNum, statusCode, body

  HealthReady = False
  On Error Resume Next
  Err.Clear
  Set http = CreateObject("WinHttp.WinHttpRequest.5.1")
  If Err.Number <> 0 Or http Is Nothing Then
    Err.Clear
    Set http = CreateObject("MSXML2.XMLHTTP")
  End If
  If Err.Number <> 0 Or http Is Nothing Then
    Exit Function
  End If

  Err.Clear
  http.SetTimeouts 500, 500, 1000, 1500
  Err.Clear
  http.Open "GET", "http://127.0.0.1:8080/api/health", False
  http.Send
  errNum = Err.Number
  If errNum <> 0 Then Exit Function

  statusCode = http.Status
  body = "" & http.responseText
  If statusCode >= 200 And statusCode < 300 Then
    If LooksLikeAiPos(body) Then HealthReady = True
  End If
End Function

Function WaitForHealth(timeoutMs, pollMs)
  Dim elapsed
  elapsed = 0
  WaitForHealth = False
  Do While elapsed <= timeoutMs
    If HealthReady() Then
      WaitForHealth = True
      Exit Function
    End If
    WScript.Sleep pollMs
    elapsed = elapsed + pollMs
  Loop
End Function

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
  ' Prefer console interpreters that serve Local Bridge reliably.
  ' Do not use pythonw.exe.
  candidates = Array( _
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
