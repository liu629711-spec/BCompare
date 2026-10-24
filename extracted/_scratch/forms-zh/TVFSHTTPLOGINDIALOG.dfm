object VfsHttpLoginDialog: TVfsHttpLoginDialog
  Caption = 'Authentication Required'
  ClientHeight = 177
  ClientWidth = 435
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object PromptLbl: TUiLabel
    Left = 8
    Top = 8
    Width = 419
    Height = 13
    Caption = '%'
    WordWrap = True
  end
  object UsernameLbl: TUiLabel
    Left = 8
    Top = 29
    Height = 13
    Caption = '&Username:'
    FocusControl = UsernameEdit
  end
  object PasswordLbl: TUiLabel
    Left = 8
    Top = 75
    Height = 13
    Caption = '&Password:'
    FocusControl = PasswordEdit
  end
  object UsernameEdit: TUiEdit
    Left = 8
    Top = 46
    Width = 419
    Height = 21
    TabOrder = 0
  end
  object PasswordEdit: TUiEdit
    Left = 8
    Top = 92
    Width = 419
    Height = 21
    TabOrder = 1
    EchoMode = emPassword
  end
  object SaveCredentialsEdit: TUiCheckBox
    Left = 8
    Top = 121
    Height = 17
    Caption = '&Save credentials'
    TabOrder = 2
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 138
    Width = 435
    TabOrder = 3
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
