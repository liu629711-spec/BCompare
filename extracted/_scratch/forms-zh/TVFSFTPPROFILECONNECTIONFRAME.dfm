object VfsFtpProfileConnectionFrame: TVfsFtpProfileConnectionFrame
  HelpType = htKeyword
  HelpKeyword = 'ProfileFtpConnection'
  Caption = 'Connection'
  object MaxConnectionsLbl: TUiLabel
    Left = 8
    Top = 33
    Height = 13
    Caption = '&Simultaneous connections:'
    FocusControl = MaxConnectionsEdit
  end
  object ReadTimeoutLbl: TUiLabel
    Left = 8
    Top = 79
    Height = 13
    Caption = '&Read timeout (seconds):'
    FocusControl = ReadTimeoutEdit
  end
  object DataPortMinLbl: TUiLabel
    Left = 24
    Top = 171
    Height = 13
    Caption = '&Min:'
    FocusControl = DataPortMinEdit
  end
  object DataPortMaxLbl: TUiLabel
    Left = 127
    Top = 171
    Height = 13
    Caption = 'Ma&x:'
    FocusControl = DataPortMaxEdit
  end
  object TLSVersionMinLbl: TUiLabel
    Left = 24
    Top = 284
    Height = 13
    Caption = 'M&in:'
    FocusControl = TLSVersionMinEdit
  end
  object TLSVersionMaxLbl: TUiLabel
    Left = 127
    Top = 284
    Height = 13
    Caption = 'Max:'
    FocusControl = TLSVersionMaxEdit
  end
  object MaxConnectionsEdit: TUiSpinEdit
    Left = 8
    Top = 50
    Width = 50
    Height = 21
    Max = 10
    MaxLength = 2
    Min = 1
    Position = 1
    TabOrder = 1
    OnChange = SomethingChangedClick
  end
  object ReadTimeoutEdit: TUiSpinEdit
    Left = 8
    Top = 96
    Width = 50
    Height = 21
    TabOrder = 2
    OnChange = SomethingChangedClick
  end
  object PassiveEdit: TUiCheckBox
    Left = 8
    Top = 125
    Height = 17
    Caption = '&Passive transfers (PASV)'
    TabOrder = 3
    OnClick = SomethingChangedClick
  end
  object DataPortLimitedEdit: TUiCheckBox
    Left = 8
    Top = 146
    Height = 17
    Caption = '&Limit ports used for active transfers (PORT):'
    TabOrder = 4
    OnClick = SomethingChangedClick
  end
  object DataPortMinEdit: TUiNumEdit
    Left = 48
    Top = 167
    Width = 63
    Height = 21
    MaxIntValue = 65535
    MaxLength = 5
    TabOrder = 5
    OnChange = SomethingChangedClick
  end
  object DataPortMaxEdit: TUiNumEdit
    Left = 155
    Top = 167
    Width = 63
    Height = 21
    MaxIntValue = 65535
    MaxLength = 5
    TabOrder = 6
    OnChange = SomethingChangedClick
  end
  object UseHOSTEdit: TUiCheckBox
    Left = 8
    Top = 196
    Height = 17
    Caption = 'Use &HOST before login'
    TabOrder = 7
    OnClick = SomethingChangedClick
  end
  object ClearControlChannelEdit: TUiCheckBox
    Left = 8
    Top = 217
    Height = 17
    Caption = 'Clear &control channel (SSL only)'
    TabOrder = 8
    OnClick = SomethingChangedClick
  end
  object ClearDataChannelEdit: TUiCheckBox
    Left = 8
    Top = 238
    Height = 17
    Caption = 'Clear da&ta channel (SSL only)'
    TabOrder = 9
    OnClick = SomethingChangedClick
  end
  object TLSVersionLimitedEdit: TUiCheckBox
    Left = 8
    Top = 259
    Height = 17
    Caption = 'Limit TLS/SSL &versions:'
    TabOrder = 10
    OnClick = SomethingChangedClick
  end
  object TLSVersionMinEdit: TUiComboBox
    Left = 48
    Top = 280
    Width = 63
    Height = 21
    Style = csDropDownList
    TabOrder = 11
    OnChange = TLSVersionMinEditChange
  end
  object TLSVersionMaxEdit: TUiComboBox
    Left = 155
    Top = 280
    Width = 63
    Height = 21
    Style = csDropDownList
    TabOrder = 12
    OnChange = TLSVersionMaxEditChange
  end
end
