object KeyUpgradeDialog: TKeyUpgradeDialog
  Caption = 'Beyond Compare %d Key Detected'
  ClientHeight = 115
  ClientWidth = 345
  OnCreate = FormCreate
  PixelsPerInch = 96
  TextHeight = 13
  object Image: TUiDlgIcon
    Left = 16
    Top = 16
    IconType = diError
  end
  object Lbl: TUiLabel
    Left = 64
    Top = 16
    Width = 273
    Height = 39
    Caption = 'This appears to be a version %0:d key, which will not work with version %1:d.  For information on upgrading your license, please visit:'
    WordWrap = True
  end
  object LinkLbl: TUiLinkLabel
    Left = 80
    Top = 63
    Height = 13
    Caption = '%'
    URL = '%'
    OnClick = LinkClick
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 76
    Width = 345
    TabOrder = 0
    object CloseBtn: TUiCloseBtn
    end
  end
end
