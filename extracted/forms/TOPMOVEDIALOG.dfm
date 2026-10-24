object OpMoveDialog: TOpMoveDialog
  HelpType = htKeyword
  HelpKeyword = 'OpMove'
  Caption = 'Move to Side'
  ClientHeight = 381
  OnClose = FormClose
  PixelsPerInch = 96
  TextHeight = 13
  object SelectionPanel: TUiPanel
    object WindowShape: TUiWindowShape
      LeftImageIndex = imgMoveRight
      RightImageIndex = imgMoveLeft
    end
  end
  object ActionPanel: TUiPanel
    Height = 50
    object ActionDescLbl: TUiLabel
      Left = 8
      Top = 29
      Height = 13
      Caption = 'Move selected files, folders.'
    end
  end
  object FilteredWarnPanel: TUiPanel
    Top = 197
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
    Top = 317
    Height = 64
    object DontShowAgainBevel: TUiBevel
      Left = 0
      Top = 39
      Width = 393
      Height = 2
      Shape = bsTopLine
    end
    object DontShowAgainEdit: TUiCheckBox
      Left = 8
      Top = 43
      Height = 17
      Caption = '&Don''t show again'
      TabOrder = 3
    end
  end
end
