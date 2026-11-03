Imports System.Drawing
Imports System.Windows.Forms

<Global.Microsoft.VisualBasic.CompilerServices.DesignerGenerated()> _
Partial Class frmKuid
    Inherits Form

    'Form overrides dispose to clean up the component list.
    <System.Diagnostics.DebuggerNonUserCode()> _
    Protected Overrides Sub Dispose(ByVal disposing As Boolean)
        Try
            If disposing AndAlso components IsNot Nothing Then
                components.Dispose()
            End If
        Finally
            MyBase.Dispose(disposing)
        End Try
    End Sub

    'Required by the Windows Form Designer
    Private components As System.ComponentModel.IContainer

    'NOTE: The following procedure is required by the Windows Form Designer
    'It can be modified using the Windows Form Designer.  
    'Do not modify it using the code editor.
    <System.Diagnostics.DebuggerStepThrough()> _
    Private Sub InitializeComponent()
        Dim resources As System.ComponentModel.ComponentResourceManager = New System.ComponentModel.ComponentResourceManager(GetType(frmKuid))
        txtKuid = New TextBox()
        txtHash = New TextBox()
        Label1 = New Label()
        Label2 = New Label()
        LinkLabel1 = New LinkLabel()
        Label3 = New Label()
        Label4 = New Label()
        txtHex = New TextBox()
        CheckBox1 = New CheckBox()
        SuspendLayout()
        ' 
        ' txtKuid
        ' 
        txtKuid.Location = New Point(78, 6)
        txtKuid.Margin = New Padding(4)
        txtKuid.Name = "txtKuid"
        txtKuid.Size = New Size(258, 27)
        txtKuid.TabIndex = 0
        txtKuid.Text = "<kuid2:474195:123456:1>"
        ' 
        ' txtHash
        ' 
        txtHash.Location = New Point(78, 69)
        txtHash.Margin = New Padding(4)
        txtHash.Name = "txtHash"
        txtHash.ReadOnly = True
        txtHash.Size = New Size(258, 27)
        txtHash.TabIndex = 1
        txtHash.Text = "hash-CB"
        ' 
        ' Label1
        ' 
        Label1.AutoSize = True
        Label1.Location = New Point(4, 9)
        Label1.Name = "Label1"
        Label1.Size = New Size(59, 20)
        Label1.TabIndex = 2
        Label1.Text = "KUID:"
        ' 
        ' Label2
        ' 
        Label2.AutoSize = True
        Label2.Location = New Point(4, 72)
        Label2.Name = "Label2"
        Label2.Size = New Size(67, 20)
        Label2.TabIndex = 3
        Label2.Text = "HASH:"
        ' 
        ' LinkLabel1
        ' 
        LinkLabel1.AutoSize = True
        LinkLabel1.Font = New Font("Microsoft Sans Serif", 7.8F, FontStyle.Regular, GraphicsUnit.Point, CByte(0))
        LinkLabel1.Location = New Point(69, 149)
        LinkLabel1.Name = "LinkLabel1"
        LinkLabel1.Size = New Size(200, 16)
        LinkLabel1.TabIndex = 12
        LinkLabel1.TabStop = True
        LinkLabel1.Text = "https://github.com/SilverGreen93"
        ' 
        ' Label3
        ' 
        Label3.AutoSize = True
        Label3.Font = New Font("Microsoft Sans Serif", 7.8F, FontStyle.Regular, GraphicsUnit.Point, CByte(0))
        Label3.Location = New Point(99, 132)
        Label3.Name = "Label3"
        Label3.Size = New Size(141, 16)
        Label3.TabIndex = 11
        Label3.Text = "SilverGreen93 (c) 2026"
        ' 
        ' Label4
        ' 
        Label4.AutoSize = True
        Label4.Location = New Point(4, 41)
        Label4.Name = "Label4"
        Label4.Size = New Size(53, 20)
        Label4.TabIndex = 14
        Label4.Text = "HEX:"
        ' 
        ' txtHex
        ' 
        txtHex.Location = New Point(78, 38)
        txtHex.Margin = New Padding(4)
        txtHex.MaxLength = 24
        txtHex.Name = "txtHex"
        txtHex.Size = New Size(258, 27)
        txtHex.TabIndex = 13
        txtHex.Text = "53 3C 07 02 40 E2 01 00"
        ' 
        ' CheckBox1
        ' 
        CheckBox1.AutoSize = True
        CheckBox1.Font = New Font("Microsoft Sans Serif", 10.2F, FontStyle.Regular, GraphicsUnit.Point, CByte(0))
        CheckBox1.Location = New Point(112, 105)
        CheckBox1.Name = "CheckBox1"
        CheckBox1.Size = New Size(128, 24)
        CheckBox1.TabIndex = 15
        CheckBox1.Text = "Reverse kuid"
        CheckBox1.UseVisualStyleBackColor = True
        ' 
        ' frmKuid
        ' 
        AutoScaleDimensions = New SizeF(11F, 20F)
        AutoScaleMode = AutoScaleMode.Font
        ClientSize = New Size(349, 180)
        Controls.Add(CheckBox1)
        Controls.Add(Label4)
        Controls.Add(txtHex)
        Controls.Add(LinkLabel1)
        Controls.Add(Label3)
        Controls.Add(Label2)
        Controls.Add(Label1)
        Controls.Add(txtHash)
        Controls.Add(txtKuid)
        Font = New Font("Microsoft Sans Serif", 10.2F, FontStyle.Bold, GraphicsUnit.Point, CByte(0))
        FormBorderStyle = FormBorderStyle.FixedSingle
        Icon = CType(resources.GetObject("$this.Icon"), Icon)
        Margin = New Padding(4)
        MaximizeBox = False
        Name = "frmKuid"
        Text = "Kuid2Hash v2.0"
        ResumeLayout(False)
        PerformLayout()

    End Sub

    Friend WithEvents txtKuid As TextBox
    Friend WithEvents txtHash As TextBox
    Friend WithEvents Label1 As Label
    Friend WithEvents Label2 As Label
    Friend WithEvents LinkLabel1 As LinkLabel
    Friend WithEvents Label3 As Label
    Friend WithEvents Label4 As Label
    Friend WithEvents txtHex As TextBox
    Friend WithEvents CheckBox1 As CheckBox
End Class
