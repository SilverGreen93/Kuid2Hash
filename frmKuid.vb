Imports System.Globalization

Public Class frmKuid

    ''' <summary>
    ''' Translates hexadecimal kuids to string
    ''' </summary>
    ''' <param name="kuid">Byte-array kuid</param>
    ''' <returns>Kuid string</returns>
    Function HexToKuid(ByVal kuid As Byte()) As String
        Dim rstring As String = "<kuid"
        Dim ubytes(3), cbytes(3) As Byte
        Dim version As Integer
        Dim uInt As Integer

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
    ''' <param name="kuid">The kuid as string</param>
    ''' <returns>The kuid as 8 bytes</returns>
    ''' <remarks></remarks>
    Function KuidToHex(ByVal kuid As String) As Byte()
        Dim num(2) As Integer                           'variable to store kuid parts
        Dim ubytes(3), cbytes(3) As Byte                'user bytes and content bytes
        Dim str() As String                             'split kuid to tokens
        Dim rbytes(7) As Byte                           'returned bytes

        If kuid = "" Then
            'MessageBox.Show("NULL kuid encountered!", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
            'err = True
            Return {0, 0, 0, 0, 0, 0, 0, 0}
        End If

        str = System.Text.RegularExpressions.Regex.Split(kuid, ":")

        If str.Length < 3 Then
            'MessageBox.Show("Invalid kuid encountered!", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
            Return {0, 0, 0, 0, 0, 0, 0, 0}
        End If

        Try
            'parse the kuid parts (skip first) and convert to integers
            For i As Integer = 1 To IIf(str.Length > 4, 4, str.Length) - 1
                num(i - 1) = Val(str(i))
            Next

            'get the bytes from integers
            ubytes = BitConverter.GetBytes(num(0))
            cbytes = BitConverter.GetBytes(num(1))
            If (num(2) > 0 AndAlso num(2) < 128 AndAlso num(0) >= 0) Then 'check if uid is negative
                ubytes(3) = ubytes(3) Xor (CByte(num(2)) << 1)  'add the version number to byte 4 of uid
            End If

            'merge bytes
            For i As Integer = 0 To 3
                rbytes(i) = ubytes(i)
                rbytes(i + 4) = cbytes(i)
            Next
        Catch ex As Exception
            MessageBox.Show(ex.ToString, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
        End Try

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
            'calculate hash using xor
            For i As Integer = 0 To 7
                hash(0) = hash(0) Xor kuid(i)
            Next
            'version needs to be ignored, so xor that out, only if uid is positive
            If (kuid(3) And (1 << 0)) = 0 Then
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
    ''' <returns>8 byte array</returns>
    Function ConvertHex(ByVal t As String) As Byte()
        Dim data(7) As Byte
        Dim s() As String = t.Split({" "c, "-"c, ":"c, ","c})
        'data = New Byte(s.Length - 1) {}
        For i As Integer = 0 To s.Length - 1
            If Not Byte.TryParse(s(i), NumberStyles.HexNumber, CultureInfo.CurrentCulture, data(i)) Then
                data(i) = 0
                'MsgBox("error converting!", MsgBoxStyle.Information)
            End If
        Next
        Return data
    End Function

    Private Sub TextBox1_TextChanged(sender As Object, e As EventArgs) Handles txtKuid.TextChanged
        If txtKuid.Focused = True Then
            txtHash.Text = "hash-" & BitConverter.ToString(computeHash(KuidToHex(txtKuid.Text)))
            txtHex.Text = BitConverter.ToString(KuidToHex(txtKuid.Text)).Replace("-"c, " "c)
        End If
    End Sub

    Private Sub LinkLabel1_LinkClicked(sender As Object, e As LinkLabelLinkClickedEventArgs) Handles LinkLabel1.LinkClicked
        Process.Start("http://vvmm.freeforums.org/")
    End Sub

    Private Sub TextBox3_TextChanged(sender As Object, e As EventArgs) Handles txtHex.TextChanged
        If txtHex.Focused = True Then
            txtKuid.Text = HexToKuid(ConvertHex(txtHex.Text))
            txtHash.Text = "hash-" & BitConverter.ToString(computeHash(KuidToHex(txtKuid.Text)))
        End If
    End Sub
End Class
