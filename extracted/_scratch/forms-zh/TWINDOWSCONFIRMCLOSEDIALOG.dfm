object WindowsConfirmCloseDialog: TWindowsConfirmCloseDialog
  Caption = 'Confirm'
  ClientHeight = 112
  ClientWidth = 321
  PixelsPerInch = 96
  TextHeight = 13
  object Image: TUiDlgIcon
    Left = 16
    Top = 16
    IconType = diConfirmation
  end
  object Lbl: TUiLabel
    Left = 64
    Top = 24
    Height = 13
    Caption = 'Close all windows?'
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 48
    Width = 321
    Height = 64
    TabOrder = 0
    object DontShowAgainBevel: TUiBevel
      Left = 0
      Top = 39
      Width = 321
      Height = 2
      Shape = bsTopLine
    end
    object OkBtn: TUiOkBtn
      Caption = '&Yes'
    end
    object CancelBtn: TUiCancelBtn
    end
    object DontShowAgainEdit: TUiCheckBox
      Left = 8
      Top = 43
      Height = 17
      Caption = '&Don''t show again'
      TabOrder = 2
    end
  end
end
