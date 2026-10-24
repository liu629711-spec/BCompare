object VfsFtpProfileServerFrame: TVfsFtpProfileServerFrame
  HelpType = htKeyword
  HelpKeyword = 'ProfileFtpServer'
  Caption = 'Server'
  object CodePageLbl: TUiLabel
    Left = 8
    Top = 58
    Height = 13
    Caption = '&Encoding:'
    FocusControl = CodePageEdit
  end
  object TimeZoneLbl: TUiLabel
    Left = 8
    Top = 104
    Height = 13
    Caption = 'Time &zone:'
    FocusControl = TimeZoneEdit
  end
  object CustomInitCommandsLbl: TUiLabel
    Left = 8
    Top = 150
    Height = 13
    Caption = 'Custom &login commands:'
    FocusControl = CustomInitCommandsEdit
  end
  object CaseSensitiveEdit: TUiCheckBox
    Left = 8
    Top = 33
    Height = 17
    Caption = 'Filenames are &case sensitive'
    TabOrder = 1
    OnClick = SomethingChangedClick
  end
  object CodePageEdit: TUiCodePageEdit
    Left = 8
    Top = 75
    Width = 239
    Height = 21
    TabOrder = 2
    OnChange = SomethingChangedClick
    AllowUtf16 = False
  end
  object TimeZoneEdit: TUiTimeZoneEdit
    Left = 8
    Top = 121
    Width = 239
    Height = 21
    TabOrder = 3
    OnChange = SomethingChangedClick
  end
  object CustomInitCommandsEdit: TUiMemo
    Left = 8
    Top = 167
    Width = 239
    Height = 134
    TabOrder = 4
    OnChange = SomethingChangedClick
  end
end
