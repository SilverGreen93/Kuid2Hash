Imports System.Globalization

''' <summary>
''' Pure kuid conversion and hashing logic, decoupled from the WinForms UI.
''' All methods are shared (static) and free of any Windows Forms dependency, so they can be
''' reused by the console entry point, the GUI, and the test suite.
''' </summary>
Public NotInheritable Class KuidConverter

    Private Sub New()
    End Sub

    ''' <summary>
    ''' Translates a binary kuid to its string form (e.g. "<kuid2:68787:1097:2>").
    ''' </summary>
    ''' <param name="kuid">8-byte kuid, or 4 bytes for a uid -1 kuid (content id only)</param>
    ''' <returns>The kuid as a bracketed string</returns>
    Public Shared Function HexToKuid(ByVal kuid As Byte()) As String
        If kuid Is Nothing OrElse (kuid.Length <> 8 AndAlso kuid.Length <> 4) Then
            Throw New ArgumentException("kuid must contain exactly 8 bytes, or 4 bytes for a uid -1 kuid.", "kuid")
        End If

        Dim rstring As String = "<kuid"
        Dim ubytes(3), cbytes(3) As Byte
        Dim version As Integer
        Dim uInt As Integer

        'a 4 byte input is the content id of a uid -1 kuid (the FF FF FF FF user part is implicit)
        If kuid.Length = 4 Then
            Array.Copy(kuid, 0, cbytes, 0, 4)
            uInt = -1
        Else
            Array.Copy(kuid, 0, ubytes, 0, 4)
            Array.Copy(kuid, 4, cbytes, 0, 4)

            If (ubytes(3) And (1 << 0)) <> 0 Then
                'negative user id, ignore version
                version = 0
            Else
                version = Convert.ToInt32(ubytes(3) >> 1)
                ubytes(3) = ubytes(3) And &H1
            End If

            uInt = BitConverter.ToInt32(ubytes, 0)
        End If

        'a uid of -1 (FF FF FF FF) is still printed with its user part: "<kuid:-1:...>"

        If version <> 0 Then
            rstring &= "2:"
        Else
            rstring &= ":"
        End If

        rstring &= uInt
        rstring &= ":"
        rstring &= BitConverter.ToInt32(cbytes, 0)

        If version <> 0 Then
            rstring &= ":" & version
        End If

        rstring &= ">"
        Return rstring
    End Function

    ''' <summary>
    ''' Translates a kuid string (e.g. "kuid 68787 1097", "<kuid2:68787:1097:3>", or "<kuid:-1:1097>")
    ''' to its binary form.
    ''' </summary>
    ''' <param name="kuid">The kuid as string</param>
    ''' <returns>8 bytes (4 user + 4 content), or only the 4 content id bytes when the uid is -1</returns>
    Public Shared Function KuidToHex(ByVal kuid As String) As Byte()
        Dim num(2) As Integer                           'variable to store kuid parts
        Dim ubytes(3), cbytes(3) As Byte                'user bytes and content bytes
        Dim str() As String                             'split kuid to tokens
        Dim rbytes(7) As Byte                           'returned bytes

        If String.IsNullOrEmpty(kuid) Then
            Throw New ArgumentException("kuid must not be empty.", "kuid")
        End If

        'strip any surrounding angle brackets emitted by HexToKuid (e.g. "<kuid2:...>")
        kuid = kuid.Trim("<"c, ">"c).Trim()

        'split on colons and/or whitespace so both "kuid:68787:1097" and "kuid 68787 1097" are accepted
        str = System.Text.RegularExpressions.Regex.Split(kuid, "[:\s]+")
        str = Array.FindAll(str, Function(t) Not String.IsNullOrEmpty(t))

        If str.Length < 3 Then
            Throw New ArgumentException("Invalid kuid: expected at least 'kuid uid cid' (e.g. '<kuid:-1:1097>').", "kuid")
        End If

        'parse the numeric parts (skip the leading tag) and convert to integers
        For i As Integer = 1 To IIf(str.Length > 4, 4, str.Length) - 1
            If Not Integer.TryParse(str(i), NumberStyles.Integer, CultureInfo.InvariantCulture, num(i - 1)) Then
                Throw New FormatException("Invalid kuid part: '" & str(i) & "'.")
            End If
        Next

        'get the bytes from integers (uid -1 is FF FF FF FF)
        ubytes = BitConverter.GetBytes(num(0))
        cbytes = BitConverter.GetBytes(num(1))
        If (num(2) > 0 AndAlso num(2) < 128 AndAlso num(0) >= 0) Then 'check if uid is negative
            ubytes(3) = ubytes(3) Xor (CByte(num(2)) << 1)  'add the version number to byte 4 of uid
        End If

        'a uid of -1 drops the FF FF FF FF user part: only the content id bytes are returned
        If num(0) = -1 Then
            Return cbytes
        End If

        'merge bytes (always exactly 8: 4 user + 4 content)
        For i As Integer = 0 To 3
            rbytes(i) = ubytes(i)
            rbytes(i + 4) = cbytes(i)
        Next

        Return rbytes
    End Function

    ''' <summary>
    ''' Computes the hash of a kuid (xor of all bytes, with the version bit xored back out
    ''' for positive 8-byte kuids).
    ''' </summary>
    ''' <param name="kuid">8-byte kuid, or 4 bytes for a uid -1 kuid</param>
    ''' <returns>One byte – the hash code</returns>
    Public Shared Function ComputeHash(ByVal kuid As Byte()) As Byte
        Dim hash As Byte = &H0

        'calculate hash using xor; a 4 byte input is the content id of a uid -1 kuid,
        'whose implicit FF FF FF FF user part xors to zero and does not affect the hash
        For i As Integer = 0 To IIf(kuid.Length = 4, 3, 7)
            hash = hash Xor kuid(i)
        Next
        'version needs to be ignored, so xor that out, only if uid is positive (8 byte kuids only)
        If kuid.Length = 8 AndAlso (kuid(3) And (1 << 0)) = 0 Then
            hash = hash Xor kuid(3)
        End If

        Return hash
    End Function

    ''' <summary>
    ''' Converts a hex string (space/dash/colon/comma separated) to a byte array.
    ''' </summary>
    ''' <param name="t">Hex string, e.g. "B3 0C 01 00 49 04 00 00" or "39 02 00 00"</param>
    ''' <returns>8 bytes (or 4 bytes for a uid -1 kuid)</returns>
    Public Shared Function ConvertHex(ByVal t As String) As Byte()
        If String.IsNullOrEmpty(t) Then
            Throw New ArgumentException("Hex string must not be empty.", "t")
        End If

        Dim s() As String = t.Split({" "c, "-"c, ":"c, ","c}, StringSplitOptions.RemoveEmptyEntries)
        '4 bytes is the content id of a uid -1 kuid (the FF FF FF FF user part is implicit)
        If s.Length <> 8 AndAlso s.Length <> 4 Then
            Throw New ArgumentException("Expected exactly 8 hex bytes (or 4 for a uid -1 kuid), got " & s.Length & ".", "t")
        End If

        Dim data(s.Length - 1) As Byte
        For i As Integer = 0 To s.Length - 1
            If Not Byte.TryParse(s(i), NumberStyles.HexNumber, CultureInfo.InvariantCulture, data(i)) Then
                Throw New FormatException("Invalid hex byte: '" & s(i) & "' in '" & t & "'.")
            End If
        Next
        Return data
    End Function

    ''' <summary>
    ''' Reverses the UID with the CID (for map files): a-b-c-d-e-f-g-h -> e-f-g-h-a-b-c-d.
    ''' </summary>
    ''' <param name="kuid">8-byte kuid</param>
    ''' <returns>The reversed 8-byte kuid</returns>
    Public Shared Function RevKuid(ByVal kuid As Byte()) As Byte()
        Dim rbytes(7) As Byte   'returned bytes

        For i As Integer = 0 To 3
            rbytes(i) = kuid(i + 4)
            rbytes(i + 4) = kuid(i)
        Next

        Return rbytes
    End Function

End Class
