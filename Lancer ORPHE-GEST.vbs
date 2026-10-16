Option Explicit

Dim shell, fso, projectDir, scriptPath, pythonwPath, command
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
scriptPath = fso.BuildPath(projectDir, "fif.py")

If Not fso.FileExists(scriptPath) Then
    MsgBox "Le fichier fif.py est introuvable dans :" & vbCrLf & projectDir, _
        vbCritical, "ORPHE - GEST"
    WScript.Quit 1
End If

pythonwPath = FindPythonw(fso, shell, projectDir)
If pythonwPath = "" Then
    MsgBox "Python est introuvable. Installe Python et les dépendances du projet, " & _
        "puis réessaie.", vbCritical, "ORPHE - GEST"
    WScript.Quit 1
End If

command = """" & pythonwPath & """ """ & scriptPath & """"
shell.Run command, 1, False

Function FindPythonw(fileSystem, windowsShell, folder)
    Dim candidates, candidate, searchPath, pathEntry, executable

    candidates = Array( _
        fileSystem.BuildPath(folder, ".venv\Scripts\pythonw.exe"), _
        fileSystem.BuildPath(folder, "venv\Scripts\pythonw.exe") _
    )
    For Each candidate In candidates
        If fileSystem.FileExists(candidate) Then
            FindPythonw = candidate
            Exit Function
        End If
    Next

    searchPath = windowsShell.ExpandEnvironmentStrings("%PATH%")
    For Each pathEntry In Split(searchPath, ";")
        pathEntry = Replace(pathEntry, """", "")
        If pathEntry <> "" Then
            executable = fileSystem.BuildPath(pathEntry, "pythonw.exe")
            If fileSystem.FileExists(executable) Then
                FindPythonw = executable
                Exit Function
            End If
        End If
    Next
    FindPythonw = ""
End Function
