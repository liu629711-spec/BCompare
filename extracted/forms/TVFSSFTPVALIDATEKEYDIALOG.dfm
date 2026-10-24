object VfsSftpValidateKeyDialog: TVfsSftpValidateKeyDialog
  Caption = 'Unknown Host Key'
  ClientHeight = 157
  ClientWidth = 465
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object Image: TUiDlgIcon
    Left = 16
    Top = 16
    IconType = diWarning
  end
  object ValidateKeyLbl: TUiLabel
    Left = 64
    Top = 16
    Width = 393
    Height = 13
    Caption = 'The server''s host key was not found in the trusted cache.'
    WordWrap = True
  end
  object HostLbl: TUiLabel
    Left = 72
    Top = 42
    Height = 13
    Caption = 'Host:'
  end
  object HostValueLbl: TUiLabel
    Left = 131
    Top = 42
    Height = 13
    Caption = '%'
  end
  object FingerprintLbl: TUiLabel
    Left = 72
    Top = 59
    Height = 13
    Caption = 'Fingerprint:'
  end
  object FingerprintValueLbl: TUiLabel
    Left = 131
    Top = 59
    Height = 13
    Caption = '%'
  end
  object AddToCacheLbl: TUiLabel
    Left = 64
    Top = 80
    Height = 13
    Caption = 'Trust this host and continue connecting?'
  end
  object AddToCacheEdit: TUiCheckBox
    Left = 64
    Top = 101
    Height = 17
    Caption = '&Add host key to trusted cache'
    TabOrder = 0
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 118
    Width = 465
    TabOrder = 1
    object OkBtn: TUiOkBtn
      Caption = '&Connect'
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
