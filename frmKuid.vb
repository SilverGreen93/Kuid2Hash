Imports System.Diagnostics
Imports System.Drawing
Imports System.Windows.Forms

Public Partial Class frmKuid

    Private Sub TextBox1_TextChanged(sender As Object, e As EventArgs) Handles txtKuid.TextChanged
        If txtKuid.Focused = True Then
            Try
                Dim kuidBytes As Byte() = KuidConverter.KuidToHex(txtKuid.Text)
                txtHash.Text = "hash-" & KuidConverter.ComputeHash(kuidBytes).ToString("X2")
                'a uid -1 kuid drops the FF FF FF FF user part from the hex display;
                'the Reverse kuid checkbox has no effect on it (KuidToHex returns only its 4 content id bytes)
                If kuidBytes.Length = 4 Then
                    txtHex.Text = BitConverter.ToString(kuidBytes).Replace("-"c, " "c)
                ElseIf CheckBox1.Checked = True Then
                    txtHex.Text = BitConverter.ToString(KuidConverter.RevKuid(kuidBytes)).Replace("-"c, " "c)
                Else
                    txtHex.Text = BitConverter.ToString(kuidBytes).Replace("-"c, " "c)
                End If
            Catch ex As Exception
                ' Ignore transient/invalid input while typing; keep the last valid values.
            End Try
        End If
    End Sub

    Private Sub LinkLabel1_LinkClicked(sender As Object, e As LinkLabelLinkClickedEventArgs) Handles LinkLabel1.LinkClicked
        Process.Start(New ProcessStartInfo("https://github.com/SilverGreen93/Kuid2Hash") With { .UseShellExecute = True })
    End Sub

    Private Sub TextBox3_TextChanged(sender As Object, e As EventArgs) Handles txtHex.TextChanged
        If txtHex.Focused = True Then
            Try
                Dim hexBytes As Byte() = KuidConverter.ConvertHex(txtHex.Text)
                'a 4 byte input is a uid -1 kuid; the Reverse kuid checkbox has no effect on it
                If CheckBox1.Checked = True AndAlso hexBytes.Length = 8 Then
                    hexBytes = KuidConverter.RevKuid(hexBytes)
                End If
                txtKuid.Text = KuidConverter.HexToKuid(hexBytes)
                txtHash.Text = "hash-" & KuidConverter.ComputeHash(KuidConverter.KuidToHex(txtKuid.Text)).ToString("X2")
            Catch ex As Exception
                ' Ignore transient/invalid input while typing; keep the last valid values.
            End Try
        End If
    End Sub

    Private Sub CheckBox1_CheckedChanged(sender As Object, e As EventArgs) Handles CheckBox1.CheckedChanged
        Try
            Dim hexBytes As Byte() = KuidConverter.ConvertHex(txtHex.Text)
            'a 4 byte input is a uid -1 kuid; the Reverse kuid checkbox has no effect on it
            If hexBytes.Length = 8 Then
                txtHex.Text = BitConverter.ToString(KuidConverter.RevKuid(hexBytes)).Replace("-"c, " "c)
            End If
        Catch ex As Exception
            ' Ignore transient/invalid input while typing; keep the last valid values.
        End Try
    End Sub

End Class
