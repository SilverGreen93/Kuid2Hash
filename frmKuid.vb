Imports System.Globalization

Public Class frmKuid

    ''' <summary>
    ''' Translates hexadecimal kuids to string
    ''' </summary>
    ''' <param name="kuid">Byte-array kuid</param>
    ''' <returns>Kuid string</returns>
    Function HexToKuid(ByVal kuid As Byte()) As String
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
        '(only the hex display drops the FF FF FF FF bytes, see TextBox1_TextChanged)

        If version <> 0 Then
            rstring = rstring & "2:"
        Else
            rstring = rstring & ":"
        End If

        rstring = rstring & uInt
        rstring = rstring & ":"
        rstring = rstring & BitConverter.ToInt32(cbytes, 0)

        If version <> 0 Then
            rstring = rstring & ":" & version
        End If

        rstring = rstring & ">"
        Return rstring
    End Function

    ''' <summary>
    ''' Translated string kuid to 8 byte kuid (for routes/sessions)
    ''' </summary>
    ''' <param name="kuid">The kuid as string (e.g. "kuid 68787 1097", "<kuid2:68787:1097:3>", or a uid -1 kuid like "<kuid:-1:1097>")</param>
    ''' <returns>The kuid as 8 bytes (a uid of -1 is stored as FF FF FF FF)</returns>
    ''' <remarks></remarks>
    Function KuidToHex(ByVal kuid As String) As Byte()
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

        'merge bytes (always exactly 8: 4 user + 4 content)
        For i As Integer = 0 To 3
            rbytes(i) = ubytes(i)
            rbytes(i + 4) = cbytes(i)
        Next

        Return rbytes

    End Function

    ''' <summary>
    ''' Computes the hash of a kuid
    ''' </summary>
    ''' <param name="kuid">Kuid to be hashed</param>
    ''' <returns>One byte - hash code</returns>
    ''' <remarks></remarks>
    Function computeHash(ByVal kuid As Byte()) As Byte()

        Dim hash As Byte() = {&H0}

        Try
            'calculate hash using xor; a 4 byte input is the content id of a uid -1 kuid,
            'whose implicit FF FF FF FF user part xors to zero and does not affect the hash
            For i As Integer = 0 To IIf(kuid.Length = 4, 3, 7)
                hash(0) = hash(0) Xor kuid(i)
            Next
            'version needs to be ignored, so xor that out, only if uid is positive (8 byte kuids only)
            If kuid.Length = 8 AndAlso (kuid(3) And (1 << 0)) = 0 Then
                hash(0) = hash(0) Xor kuid(3)
            End If

        Catch ex As Exception
            MessageBox.Show(ex.ToString, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
        End Try

        Return hash

    End Function

    ''' <summary>
    ''' Converts hex string to byte array
    ''' </summary>
    ''' <param name="t">String to be parsed</param>
    ''' <returns>8 byte array (4 bytes for a uid -1 kuid)</returns>
    Function ConvertHex(ByVal t As String) As Byte()
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
    ''' Reverses the UID with the CID (for map files)
    ''' </summary>
    ''' <param name="kuid">The kuid as 8 bytes</param>
    ''' <returns>The reversed kuid as 8 bytes</returns>
    ''' <remarks></remarks>
    Function revKuid(ByVal kuid As Byte()) As Byte()

        Dim rbytes(7) As Byte   'returned bytes

        Try
            'reverse bytes (a-b-c-d-e-f-g-h -> e-f-g-h-a-b-c-d)
            For i As Integer = 0 To 3
                rbytes(i) = kuid(i + 4)
                rbytes(i + 4) = kuid(i)
            Next
        Catch ex As Exception
            MessageBox.Show(ex.ToString, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
        End Try

        Return rbytes

    End Function

    Private Sub TextBox1_TextChanged(sender As Object, e As EventArgs) Handles txtKuid.TextChanged
        If txtKuid.Focused = True Then
            Try
                Dim kuidBytes As Byte() = KuidToHex(txtKuid.Text)
                txtHash.Text = "hash-" & BitConverter.ToString(computeHash(kuidBytes))
                'a uid -1 kuid drops the FF FF FF FF user part from the hex display;
                'the Reverse kuid checkbox has no effect on it
                If BitConverter.ToInt32(kuidBytes, 0) = -1 Then
                    txtHex.Text = BitConverter.ToString(kuidBytes, 4, 4).Replace("-"c, " "c)
                ElseIf CheckBox1.Checked = True Then
                    txtHex.Text = BitConverter.ToString(revKuid(kuidBytes)).Replace("-"c, " "c)
                Else
                    txtHex.Text = BitConverter.ToString(kuidBytes).Replace("-"c, " "c)
                End If
            Catch ex As Exception
                ' Ignore transient/invalid input while typing; keep the last valid values.
            End Try
        End If
    End Sub

    Private Sub LinkLabel1_LinkClicked(sender As Object, e As LinkLabelLinkClickedEventArgs) Handles LinkLabel1.LinkClicked
        Process.Start("https://github.com/SilverGreen93/Kuid2Hash")
    End Sub

    Private Sub TextBox3_TextChanged(sender As Object, e As EventArgs) Handles txtHex.TextChanged
        If txtHex.Focused = True Then
            Try
                Dim hexBytes As Byte() = ConvertHex(txtHex.Text)
                'a 4 byte input is a uid -1 kuid; the Reverse kuid checkbox has no effect on it
                If CheckBox1.Checked = True AndAlso hexBytes.Length = 8 Then
                    hexBytes = revKuid(hexBytes)
                End If
                txtKuid.Text = HexToKuid(hexBytes)
                txtHash.Text = "hash-" & BitConverter.ToString(computeHash(KuidToHex(txtKuid.Text)))
            Catch ex As Exception
                ' Ignore transient/invalid input while typing; keep the last valid values.
            End Try
        End If
    End Sub

    Private Sub CheckBox1_CheckedChanged(sender As Object, e As EventArgs) Handles CheckBox1.CheckedChanged
        Try
            Dim hexBytes As Byte() = ConvertHex(txtHex.Text)
            'a 4 byte input is a uid -1 kuid; the Reverse kuid checkbox has no effect on it
            If hexBytes.Length = 8 Then
                txtHex.Text = BitConverter.ToString(revKuid(hexBytes)).Replace("-"c, " "c)
            End If
        Catch ex As Exception
            ' Ignore transient/invalid input while typing; keep the last valid values.
        End Try
    End Sub

End Class
