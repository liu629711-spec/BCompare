object PixFullScreenDialog: TPixFullScreenDialog
  BorderStyle = bsNone
  ClientHeight = 448
  ClientWidth = 448
  Color = 2305582
  PopupMenu = Popup
  OnShortCut = FormShortCut
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object Image: TUiImage
    Left = 200
    Top = 200
    Width = 48
    Height = 48
  end
  object LeftPanel: TUiPanel
    Left = 8
    Top = 8
    Width = 8
    Height = 8
    Hint = 'Show Left'
    Color = 16382457
    ParentBackground = False
    TabOrder = 0
    OnClick = SideClick
  end
  object RightPanel: TUiPanel
    Left = 24
    Top = 8
    Width = 8
    Height = 8
    Hint = 'Show Right'
    Color = 16382457
    ParentBackground = False
    TabOrder = 1
    OnClick = SideClick
  end
  object CenterPanel: TUiPanel
    Left = 16
    Top = 16
    Width = 8
    Height = 8
    Hint = 'Show Difference'
    Color = 16382457
    ParentBackground = False
    TabOrder = 2
    OnClick = SideClick
  end
  object Popup: TUiPopupMenu
    Left = 40
    Top = 8
    object LeftItem: TUiMenuItem
      Caption = 'Show Left'
      ShortCut = 37
      OnClick = SideClick
    end
    object RightItem: TUiMenuItem
      Caption = 'Show Right'
      ShortCut = 39
      OnClick = SideClick
    end
    object CenterItem: TUiMenuItem
      Caption = 'Show Difference'
      ShortCut = 40
      OnClick = SideClick
    end
    object SeparatorItem: TUiSeparatorItem
    end
    object ExitItem: TUiMenuItem
      Caption = 'Exit Full Screen'
      OnClick = ExitClick
    end
  end
end
