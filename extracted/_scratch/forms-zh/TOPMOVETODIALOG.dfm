object OpMoveToDialog: TOpMoveToDialog
  HelpKeyword = 'OpMoveTo'
  Caption = 'Move to Folder'
  ClientHeight = 465
  PixelsPerInch = 96
  TextHeight = 13
  object SelectionPanel: TUiPanel
    object WindowShape: TUiWindowShape
      LeftImageIndex = imgMoveTo
      RightImageIndex = imgMoveTo
    end
  end
  object ActionPanel: TUiPanel
    object ActionDescLbl: TUiLabel
      Caption = 'Move selected files to this folder:'
    end
  end
  object FilteredWarnPanel: TUiPanel
    Height = 120
    object WarnImage: TUiDlgIcon
      Left = 8
      Top = 80
      IconType = diWarning
    end
    object WarnLbl: TUiLabel
      Left = 48
      Top = 86
      Width = 337
      Height = 13
      Caption = 'Folders with hidden items will not be moved.'
      WordWrap = True
    end
  end
  object BtnPanel: TUiBtnPanel
    Top = 426
  end
end
