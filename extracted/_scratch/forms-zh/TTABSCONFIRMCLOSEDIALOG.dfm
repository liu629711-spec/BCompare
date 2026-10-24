object TabsConfirmCloseDialog: TTabsConfirmCloseDialog
  ClientHeight = 120
  ClientWidth = 353
  OnShow = FormShow
  OnKeyDown = FormKeyDown
  PixelsPerInch = 96
  TextHeight = 13
  object Image: TUiDlgIcon
    Left = 16
    Top = 16
    IconType = diConfirmation
  end
  object Lbl: TUiLabel
    Left = 64
    Top = 16
    Width = 281
    Height = 13
    Caption = 'Do you want to close all tabs or the current tab?'
    Layout = tlCenter
    WordWrap = True
  end
  object DontShowAgainBevel: TUiBevel
    Left = 0
    Top = 95
    Width = 353
    Height = 2
    Shape = bsTopLine
  end
  object YesToAllBtn: TUiYesToAllBtn
    Left = 151
    Top = 64
    Width = 83
    Caption = 'Close All &Tabs'
    Default = True
    TabOrder = 0
    AutoSize = asRight
  end
  object YesBtn: TUiYesBtn
    Left = 241
    Top = 64
    Width = 104
    Caption = 'Close &Current Tab'
    TabOrder = 1
    AutoSize = asRight
  end
  object DontShowAgainEdit: TUiCheckBox
    Left = 8
    Top = 99
    Height = 17
    Caption = '&Always close all tabs'
    TabOrder = 2
    OnClick = DontShowAgainClick
  end
end
