object VfsWebDAVProfileGeneralFrame: TVfsWebDAVProfileGeneralFrame
  HelpType = htKeyword
  HelpKeyword = 'ProfileWebDAV'
  Caption = 'General'
  object BaseURLLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '&URL:'
    FocusControl = BaseURLEdit
  end
  object UsernameLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = 'User&name:'
    FocusControl = UsernameEdit
  end
  object PasswordLbl: TUiLabel
    Left = 131
    Top = 54
    Height = 13
    Caption = '&Password:'
    FocusControl = PasswordEdit
  end
  object SSLClientCertFileLbl: TUiLabel
    Left = 8
    Top = 100
    Height = 13
    Caption = '&SSL client certificate:'
    FocusControl = SSLClientCertFileEdit
  end
  object DescriptionLbl: TUiLabel
    Left = 8
    Top = 199
    Height = 13
    Caption = 'D&escription:'
    FocusControl = DescriptionEdit
  end
  object BaseURLEdit: TUiEdit
    Left = 8
    Top = 25
    Width = 239
    Height = 21
    TabOrder = 0
    OnChange = SomethingChangedClick
  end
  object UsernameEdit: TUiEdit
    Left = 8
    Top = 71
    Width = 115
    Height = 21
    TabOrder = 1
    OnChange = SomethingChangedClick
  end
  object PasswordEdit: TUiEdit
    Left = 131
    Top = 71
    Width = 116
    Height = 21
    TabOrder = 2
    OnChange = SomethingChangedClick
    EchoMode = emPassword
  end
  object SSLClientCertFileEdit: TUiSpecBar
    Left = 8
    Top = 117
    Width = 239
    TabOrder = 3
    OnBrowse = SSLClientCertFileEditBrowse
    OnChange = SomethingChangedClick
  end
  object SSLCreateCertBtn: TUiButton
    Left = 144
    Top = 143
    Width = 103
    Caption = '&Create Certificate'
    TabOrder = 4
    OnClick = SSLCreateCertClick
    AutoSize = asRight
  end
  object RecursiveEdit: TUiCheckBox
    Left = 8
    Top = 174
    Height = 17
    Caption = '&Recursive listings'
    TabOrder = 5
    OnClick = SomethingChangedClick
  end
  object DescriptionEdit: TUiMemo
    Left = 8
    Top = 216
    Width = 239
    Height = 85
    ScrollBars = ssVertical
    TabOrder = 6
    OnChange = SomethingChangedClick
  end
end
