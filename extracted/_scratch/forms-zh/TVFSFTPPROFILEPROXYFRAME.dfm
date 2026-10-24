object VfsFtpProfileProxyFrame: TVfsFtpProfileProxyFrame
  HelpType = htKeyword
  HelpKeyword = 'ProfileFtpProxy'
  Caption = 'Proxy'
  object ProxyTypeLbl: TUiLabel
    Left = 8
    Top = 58
    Height = 13
    Caption = 'Proxy &type:'
    FocusControl = ProxyTypeEdit
  end
  object HostLbl: TUiLabel
    Left = 8
    Top = 104
    Height = 13
    Caption = '&Host:'
    FocusControl = HostEdit
  end
  object PortLbl: TUiLabel
    Left = 198
    Top = 104
    Height = 13
    Caption = 'P&ort:'
    FocusControl = PortEdit
  end
  object UsernameLbl: TUiLabel
    Left = 8
    Top = 150
    Height = 13
    Caption = '&Username:'
    FocusControl = UsernameEdit
  end
  object PasswordLbl: TUiLabel
    Left = 131
    Top = 150
    Height = 13
    Caption = 'Pass&word:'
    FocusControl = PasswordEdit
  end
  object EnabledEdit: TUiCheckBox
    Left = 8
    Top = 33
    Height = 17
    Caption = 'Use &proxy'
    TabOrder = 1
    OnClick = SomethingChangedClick
  end
  object ProxyTypeEdit: TUiComboBox
    Left = 8
    Top = 75
    Width = 163
    Height = 21
    Style = csDropDownList
    TabOrder = 2
    OnChange = ProxyTypeEditChange
  end
  object HostEdit: TUiEdit
    Left = 8
    Top = 121
    Width = 182
    Height = 21
    TabOrder = 3
    OnChange = SomethingChangedClick
  end
  object PortEdit: TUiNumEdit
    Left = 198
    Top = 121
    Width = 49
    Height = 21
    MaxLength = 5
    TabOrder = 4
    OnChange = SomethingChangedClick
  end
  object UsernameEdit: TUiEdit
    Left = 8
    Top = 167
    Width = 115
    Height = 21
    TabOrder = 5
    OnChange = SomethingChangedClick
  end
  object PasswordEdit: TUiEdit
    Left = 131
    Top = 167
    Width = 116
    Height = 21
    TabOrder = 6
    OnChange = SomethingChangedClick
    EchoMode = emPassword
  end
end
