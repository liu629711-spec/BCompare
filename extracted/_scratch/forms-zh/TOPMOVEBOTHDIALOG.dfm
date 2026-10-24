object OpMoveBothDialog: TOpMoveBothDialog
  HelpType = htKeyword
  HelpKeyword = 'OpExchange'
  Caption = 'Exchange'
  ClientHeight = 341
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
      Caption = 'Move selected files to other side.'
    end
  end
  object FilteredWarnPanel: TUiPanel
    Top = 197
  end
  object BtnPanel: TUiBtnPanel
    Top = 277
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
