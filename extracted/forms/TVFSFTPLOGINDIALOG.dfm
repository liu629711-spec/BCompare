object VfsFtpLoginDialog: TVfsFtpLoginDialog
  ActiveControl = PasswordEdit
  Caption = '%'
  ClientHeight = 202
  ClientWidth = 435
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object SpecLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Site:'
  end
  object UsernameLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = '&Username:'
    FocusControl = UsernameEdit
  end
  object PasswordLbl: TUiLabel
    Left = 8
    Top = 100
    Height = 13
    Caption = '&Password:'
    FocusControl = PasswordEdit
  end
  object SpecPanel: TUiPanel
    Left = 8
    Top = 25
    Width = 419
    Height = 21
    Alignment = taLeftJustify
    BevelOuter = bvLowered
    TabOrder = 0
  end
  object UsernameEdit: TUiEdit
    Left = 8
    Top = 71
    Width = 419
    Height = 21
    TabOrder = 1
    OnChange = UsernameEditChange
  end
  object PasswordEdit: TUiEdit
    Left = 8
    Top = 117
    Width = 419
    Height = 21
    TabOrder = 2
    EchoMode = emPassword
  end
  object SavePasswordEdit: TUiCheckBox
    Left = 8
    Top = 146
    Height = 17
    Caption = '&Save password'
    TabOrder = 3
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 163
    Width = 435
    TabOrder = 4
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
