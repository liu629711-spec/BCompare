object OpFilteredDialog: TOpFilteredDialog
  BorderStyle = bsSizeable
  Caption = 'Hidden Items'
  ClientHeight = 327
  ClientWidth = 281
  Constraints.MinHeight = 119
  Constraints.MinWidth = 105
  OnCloseQuery = FormCloseQuery
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnResize = FormResize
  PixelsPerInch = 96
  TextHeight = 13
  object LeftBevel: TUiBevel
    Left = 0
    Top = 25
    Width = 8
    Height = 263
    Align = alLeft
    Shape = bsSpacer
  end
  object RightBevel: TUiBevel
    Left = 273
    Top = 25
    Width = 8
    Height = 263
    Align = alRight
    Shape = bsSpacer
  end
  object TopPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 281
    Height = 25
    Align = alTop
    BevelOuter = bvNone
    TabOrder = 0
    object PreviewLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'Hidden items contained in selected folder(s):'
    end
  end
  object ListBox: TUiVirtualListBox
    Left = 8
    Top = 25
    Width = 265
    Height = 263
    Align = alClient
    TabOrder = 1
    OnGetText = ListBoxGetText
  end
  object ProgressLbl: TUiStaticText
    Left = 16
    Top = 31
    Width = 238
    Height = 17
    AutoSize = False
    Caption = '%'
    Color = clWindow
    ParentColor = False
    TabOrder = 2
    Transparent = False
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 288
    Width = 281
    TabOrder = 3
    SizeGripper = True
    object CloseBtn: TUiCloseBtn
    end
  end
end
