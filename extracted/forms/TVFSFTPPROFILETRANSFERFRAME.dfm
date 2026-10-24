object VfsFtpProfileTransferFrame: TVfsFtpProfileTransferFrame
  HelpType = htKeyword
  HelpKeyword = 'ProfileFtpTransfer'
  Caption = 'Transfer'
  object TransferTypeLbl: TUiLabel
    Left = 8
    Top = 33
    Height = 13
    Caption = 'Transfer type:'
  end
  object DownloadThrottleKbpsLbl: TUiLabel
    Left = 8
    Top = 192
    Height = 13
    Caption = 'Limit do&wnload (Kbps):'
    FocusControl = DownloadThrottleKbpsEdit
  end
  object UploadThrottleKbpsLbl: TUiLabel
    Left = 8
    Top = 238
    Height = 13
    Caption = 'Limit &upload (Kbps):'
    FocusControl = UploadThrottleKbpsEdit
  end
  object AutoEdit: TUiRadioButton
    Left = 8
    Top = 50
    Height = 17
    Caption = 'Aut&o'
    TabOrder = 1
    OnClick = SomethingChangedClick
  end
  object ASCIIEdit: TUiRadioButton
    Left = 8
    Top = 71
    Height = 17
    Caption = 'A&SCII'
    TabOrder = 2
    OnClick = SomethingChangedClick
  end
  object BinaryEdit: TUiRadioButton
    Left = 8
    Top = 92
    Height = 17
    Caption = 'Bi&nary'
    TabOrder = 3
    OnClick = SomethingChangedClick
  end
  object PreserveTimestampsOnUploadEdit: TUiCheckBox
    Left = 8
    Top = 125
    Height = 17
    Caption = 'Copy &timestamps on upload'
    TabOrder = 4
    OnClick = SomethingChangedClick
  end
  object CopyUnixPermissionsOnUploadEdit: TUiCheckBox
    Left = 8
    Top = 146
    Height = 17
    Caption = 'Copy Unix &permissions on upload'
    TabOrder = 5
    OnClick = SomethingChangedClick
  end
  object CompressEdit: TUiCheckBox
    Left = 8
    Top = 167
    Height = 17
    Caption = '&Compress transfers (MODE Z)'
    TabOrder = 6
    OnClick = SomethingChangedClick
  end
  object DownloadThrottleKbpsEdit: TUiSpinEdit
    Left = 8
    Top = 209
    Width = 50
    Height = 21
    TabOrder = 7
    OnChange = SomethingChangedClick
  end
  object UploadThrottleKbpsEdit: TUiSpinEdit
    Left = 8
    Top = 255
    Width = 50
    Height = 21
    TabOrder = 8
    OnChange = SomethingChangedClick
  end
  object AggressiveOpenSSHPipeliningEdit: TUiCheckBox
    Left = 8
    Top = 284
    Height = 17
    Caption = 'Use a&ggressive uploads to OpenSSH servers'
    TabOrder = 9
    OnClick = SomethingChangedClick
  end
end
