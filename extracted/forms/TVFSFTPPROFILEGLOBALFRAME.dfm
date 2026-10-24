object VfsFtpProfileGlobalFrame: TVfsFtpProfileGlobalFrame
  HelpType = htKeyword
  HelpKeyword = 'ProfileFtpGlobal'
  Caption = 'Global'
  object EmailAddressPanel: TUiPanel
    Left = 8
    Top = 0
    Width = 239
    Height = 62
    BevelOuter = bvNone
    TabOrder = 0
    object EmailAddressLbl: TUiLabel
      Left = 0
      Top = 8
      Height = 13
      Caption = '&Email address for anonymous logins:'
      FocusControl = EmailAddressEdit
    end
    object EmailAddressEdit: TUiEdit
      Left = 0
      Top = 25
      Width = 239
      Height = 21
      TabOrder = 0
      OnChange = SomethingChangedClick
    end
  end
  object SSHPanel: TUiPanel
    Left = 8
    Top = 62
    Width = 239
    Height = 93
    BevelOuter = bvNone
    TabOrder = 1
    object SSHBevel: TUiBevel
      Left = 0
      Top = 0
      Width = 239
      Height = 1
      Align = alTop
      Shape = bsTopLine
    end
    object SSHPrivateKeyFileLbl: TUiLabel
      Left = 0
      Top = 8
      Height = 13
      Caption = 'SS&H private key file:'
      FocusControl = SSHPrivateKeyFileEdit
    end
    object SSHPrivateKeyFileEdit: TUiSpecBar
      Left = 0
      Top = 25
      Width = 239
      TabOrder = 0
      OnBrowse = AuthFileEditBrowse
      OnChange = SomethingChangedClick
    end
    object SSHCreateKeysBtn: TUiButton
      Left = 163
      Top = 54
      Width = 76
      Caption = 'Create &Keys'
      TabOrder = 1
      OnClick = SSHCreateKeysClick
      AutoSize = asRight
    end
  end
  object SSLPanel: TUiPanel
    Left = 8
    Top = 155
    Width = 239
    Height = 93
    BevelOuter = bvNone
    TabOrder = 2
    object SSLBevel: TUiBevel
      Left = 0
      Top = 0
      Width = 239
      Height = 1
      Align = alTop
      Shape = bsTopLine
    end
    object SSLClientCertFileLbl: TUiLabel
      Left = 0
      Top = 8
      Height = 13
      Caption = 'SS&L client certificate:'
      FocusControl = SSLClientCertFileEdit
    end
    object SSLClientCertFileEdit: TUiSpecBar
      Left = 0
      Top = 25
      Width = 239
      TabOrder = 0
      OnBrowse = AuthFileEditBrowse
      OnChange = SomethingChangedClick
    end
    object SSLCreateCertBtn: TUiButton
      Left = 136
      Top = 54
      Width = 103
      Caption = 'Create &Certificate'
      TabOrder = 1
      OnClick = SSLCreateCertClick
      AutoSize = asRight
    end
  end
  object ASCIITypesPanel: TUiPanel
    Left = 8
    Top = 248
    Width = 239
    Height = 61
    BevelOuter = bvNone
    TabOrder = 3
    object ASCIITypesBevel: TUiBevel
      Left = 0
      Top = 0
      Width = 239
      Height = 1
      Align = alTop
      Shape = bsTopLine
    end
    object ASCIITypesLbl: TUiLabel
      Left = 0
      Top = 8
      Height = 13
      Caption = 'A&SCII types:'
      FocusControl = ASCIITypesEdit
    end
    object ASCIITypesEdit: TUiMemo
      Left = 0
      Top = 25
      Width = 239
      Height = 28
      ScrollBars = ssVertical
      TabOrder = 0
      WordWrap = False
      OnChange = SomethingChangedClick
    end
  end
end
