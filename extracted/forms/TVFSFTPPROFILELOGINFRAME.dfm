object VfsFtpProfileLoginFrame: TVfsFtpProfileLoginFrame
  HelpType = htKeyword
  HelpKeyword = 'ProfileFtpLogin'
  Caption = 'Login'
  object SpecPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 255
    Height = 125
    Align = alTop
    BevelOuter = bvNone
    TabOrder = 0
    object ProtocolLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = '&Protocol:'
      FocusControl = ProtocolEdit
    end
    object HostLbl: TUiLabel
      Left = 137
      Top = 8
      Height = 13
      Caption = '&Host:'
      FocusControl = HostEdit
    end
    object PortLbl: TUiLabel
      Left = 198
      Top = 8
      Height = 13
      Caption = 'P&ort:'
      FocusControl = PortEdit
    end
    object UsernameLbl: TUiLabel
      Left = 8
      Top = 54
      Height = 13
      Caption = '&Username:'
      FocusControl = UsernameEdit
    end
    object PasswordLbl: TUiLabel
      Left = 131
      Top = 54
      Height = 13
      Caption = 'Pass&word:'
      FocusControl = PasswordEdit
    end
    object ProtocolEdit: TUiComboBox
      Left = 8
      Top = 25
      Width = 121
      Height = 21
      Style = csDropDownList
      TabOrder = 0
      OnChange = ProtocolEditChange
    end
    object HostEdit: TUiEdit
      Left = 137
      Top = 25
      Width = 53
      Height = 21
      TabOrder = 1
      OnChange = HostPortEditChange
      OnExit = HostEditExit
    end
    object PortEdit: TUiNumEdit
      Left = 198
      Top = 25
      Width = 49
      Height = 21
      MaxLength = 5
      TabOrder = 2
      OnChange = HostPortEditChange
    end
    object UsernameEdit: TUiEdit
      Left = 8
      Top = 71
      Width = 115
      Height = 21
      TabOrder = 3
      OnChange = UsernameEditChange
    end
    object PasswordEdit: TUiEdit
      Left = 131
      Top = 71
      Width = 116
      Height = 21
      TabOrder = 4
      OnChange = SomethingChangedClick
      EchoMode = emPassword
    end
    object SavePasswordEdit: TUiCheckBox
      Left = 8
      Top = 100
      Height = 17
      Caption = 'Sa&ve password'
      TabOrder = 5
      OnClick = SomethingChangedClick
    end
  end
  object AuthPanelView: TUiActivePanelView
    Left = 0
    Top = 125
    Width = 255
    Height = 46
    Align = alTop
    TabOrder = 1
    object SSHPanel: TUiActivePanel
      object SSHPrivateKeyFileLbl: TUiLabel
        Left = 8
        Top = 0
        Height = 13
        Caption = '&SSH private key file:'
        FocusControl = SSHPrivateKeyFileEdit
      end
      object SSHPrivateKeyFileEdit: TUiSpecBar
        Left = 8
        Top = 17
        Width = 155
        TabOrder = 0
        OnBrowse = AuthFileEditBrowse
        OnChange = SomethingChangedClick
      end
      object SSHCreateKeysBtn: TUiButton
        Left = 171
        Top = 16
        Width = 76
        Caption = 'Create &Keys'
        TabOrder = 1
        OnClick = SSHCreateKeysClick
        AutoSize = asRight
      end
    end
    object SSLPanel: TUiActivePanel
      object SSLClientCertFileLbl: TUiLabel
        Left = 8
        Top = 0
        Height = 13
        Caption = '&SSL client cert file:'
        FocusControl = SSLClientCertFileEdit
      end
      object SSLClientCertFileEdit: TUiSpecBar
        Left = 8
        Top = 17
        Width = 128
        TabOrder = 0
        OnBrowse = AuthFileEditBrowse
        OnChange = SomethingChangedClick
      end
      object SSLCreateCertBtn: TUiButton
        Left = 144
        Top = 16
        Width = 103
        Caption = 'Create &Certificate'
        TabOrder = 1
        OnClick = SSLCreateCertClick
        AutoSize = asRight
      end
    end
  end
  object PanelView: TUiActivePanelView
    Left = 0
    Top = 171
    Width = 255
    Height = 138
    Align = alClient
    TabOrder = 2
    object DescriptionPanel: TUiActivePanel
      object DescriptionLbl: TUiLabel
        Left = 8
        Top = 0
        Height = 13
        Caption = 'D&escription:'
        FocusControl = DescriptionEdit
      end
      object DescriptionEdit: TUiMemo
        Left = 8
        Top = 17
        Width = 239
        Height = 113
        ScrollBars = ssVertical
        TabOrder = 0
        OnChange = SomethingChangedClick
      end
    end
    object BrowsePanel: TUiActivePanel
      object BrowseFrame: TProfileBrowseRemoteFrame
        Left = 8
        Top = 31
        Width = 239
        Height = 99
        TabOrder = 0
        object TreeView: TUiTreeView
          Width = 239
          Height = 99
        end
      end
      object BrowseBtn: TUiButton
        Left = 8
        Top = 0
        Caption = 'Connect && &Browse'
        TabOrder = 1
        OnClick = BrowseClick
        AutoSize = asLeft
      end
    end
  end
end
