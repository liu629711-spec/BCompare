object VfsSftpValidateChangedKeyDialog: TVfsSftpValidateChangedKeyDialog
  Caption = 'Changed Host Key'
  ClientHeight = 204
  PixelsPerInch = 96
  TextHeight = 13
  object Image: TUiDlgIcon
    IconType = diError
  end
  object WarnLbl: TUiLabel
    Left = 64
    Top = 16
    Height = 13
    Caption = 'WARNING - Potential Security Breach'
    FontStyle = [fsBold]
  end
  object ValidateKeyLbl: TUiLabel
    Top = 37
    Height = 52
    Caption = 'The server''s host key does not match the one stored in the trusted cache.  This means that either the server administrator has changed the host key, or you have connected to another computer pretending to be the server.'
  end
  object HostLbl: TUiLabel
    Top = 89
  end
  object HostValueLbl: TUiLabel
    Top = 89
  end
  object FingerprintLbl: TUiLabel
    Top = 106
  end
  object FingerprintValueLbl: TUiLabel
    Top = 106
  end
  object AddToCacheLbl: TUiLabel
    Top = 127
  end
  object AddToCacheEdit: TUiCheckBox
    Top = 148
    Caption = '&Replace existing host key in trusted cache'
  end
  object BtnPanel: TUiBtnPanel
    Top = 165
  end
end
