object VfsArchivePasswordDialog: TVfsArchivePasswordDialog
  Caption = 'Enter Password'
  ClientHeight = 148
  ClientWidth = 417
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object TopBevel: TUiBevel
    Left = 0
    Top = 0
    Width = 417
    Height = 8
    Align = alTop
    Shape = bsSpacer
  end
  object InvalidLbl: TUiLabel
    Left = 0
    Top = 8
    Height = 13
    Align = alTop
    Alignment = taCenter
    Caption = 'Password is incorrect.'
    FontColor = clRed
  end
  object SpecLbl: TUiLabel
    Left = 8
    Top = 25
    Height = 13
    Caption = 'Encrypted archive:'
  end
  object PasswordLbl: TUiLabel
    Left = 8
    Top = 71
    Height = 13
    Caption = '&Password:'
    FocusControl = PasswordEdit
  end
  object SpecEdit: TUiMemo
    Left = 8
    Top = 42
    Width = 401
    Height = 21
    TabStop = False
    BorderStyle = bsNone
    ParentColor = True
    ReadOnly = True
    TabOrder = 0
    WantReturns = False
    OnEnter = SpecEditEnter
    OnExit = SpecEditExit
  end
  object PasswordEdit: TUiEdit
    Left = 8
    Top = 88
    Width = 201
    Height = 21
    TabOrder = 1
    EchoMode = emPassword
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 109
    Width = 417
    TabOrder = 2
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
