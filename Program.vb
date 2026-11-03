Imports System.Globalization
Imports System.Text
Imports System.Windows.Forms

Module Program

    ''' <summary>
    ''' Entry point: with no arguments the GUI launches; with one or more arguments the app
    ''' runs in CLI mode and prints the converted kuid(s) and hash to stdout.
    ''' </summary>
    <STAThread>
    Sub Main(ByVal Optional args() As String = Nothing)
        If args Is Nothing OrElse args.Length = 0 Then
            Application.EnableVisualStyles()
            Application.SetCompatibleTextRenderingDefault(False)
            Application.Run(New frmKuid())
            Return
        End If

        'A single kuid may arrive as one quoted argument ("kuid 68787 1097") or, if the
        'shell split it, as several tokens. Re-join with spaces and treat the whole thing
        'as one kuid, unless the user clearly passed multiple separate kuids.
        Dim joined As String = String.Join(" ", args)
        Dim result As Boolean = RunCli(joined)
        If Not result Then
            Environment.ExitCode = 1
        End If
    End Sub

    ''' <summary>
    ''' Processes a single CLI argument (a kuid in string or binary form) and prints the
    ''' converted kuid, hex bytes and hash. Returns False (and prints to stderr) on error.
    ''' </summary>
    Private Function RunCli(ByVal arg As String) As Boolean
        Dim bytes As Byte()

        Try
            bytes = ParseKuid(arg)
        Catch ex As Exception
            Console.Error.WriteLine("Error: " & ex.Message)
            Return False
        End Try

        Console.WriteLine("kuid:  {0}", KuidConverter.HexToKuid(bytes))
        Console.WriteLine("hex:   {0}", BitConverter.ToString(bytes).Replace("-"c, " "c))
        Console.WriteLine("hash:  hash-{0}", KuidConverter.ComputeHash(bytes).ToString("X2"))
        Return True
    End Function

    ''' <summary>
    ''' Detects whether the argument is a binary (hex) kuid or a string kuid and parses it.
    ''' </summary>
    Private Function ParseKuid(ByVal arg As String) As Byte()
        Dim trimmed As String = arg.Trim()

        'binary format: only hex bytes (and separators) with at least 4 byte tokens -> treat as hex
        If IsHexKuid(trimmed) Then
            Return KuidConverter.ConvertHex(trimmed)
        End If

        'otherwise treat as a string kuid ("kuid 68787 1097", "<kuid2:...>", etc.)
        Return KuidConverter.KuidToHex(trimmed)
    End Function

    ''' <summary>
    ''' True when the argument looks like a hex byte sequence: splitting on the allowed
    ''' separators yields 4 or 8 tokens, every one of them a valid hex byte.
    ''' </summary>
    Private Function IsHexKuid(ByVal arg As String) As Boolean
        Dim s() As String = arg.Split({" "c, "-"c, ":"c, ","c}, StringSplitOptions.RemoveEmptyEntries)
        If (s.Length <> 8 AndAlso s.Length <> 4) Then
            Return False
        End If

        For Each token As String In s
            Dim b As Byte
            If Not Byte.TryParse(token, NumberStyles.HexNumber, CultureInfo.InvariantCulture, b) Then
                Return False
            End If
        Next

        Return True
    End Function

End Module
