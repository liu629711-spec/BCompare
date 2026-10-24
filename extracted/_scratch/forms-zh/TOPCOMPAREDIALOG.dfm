object OpCompareDialog: TOpCompareDialog
  HelpType = htKeyword
  HelpKeyword = 'OpCompare'
  Caption = 'Compare Contents'
  ClientHeight = 433
  OnClose = FormClose
  PixelsPerInch = 96
  TextHeight = 13
  object SelectionPanel: TUiPanel
    object WindowShape: TUiWindowShape
      CenterImageIndex = imgCompare
      LeftImageVisible = False
      RightImageVisible = False
    end
  end
  object ActionPanel: TUiPanel
    Height = 142
    object ActionDescLbl: TUiLabel
      Left = 8
      Top = 29
      Height = 13
      Caption = 'Compare contents of selected files, folders.'
    end
    object CRC32Edit: TUiRadioButton
      Left = 8
      Top = 50
      Height = 17
      Caption = '&CRC comparison'
      TabOrder = 0
    end
    object BinaryEdit: TUiRadioButton
      Left = 8
      Top = 71
      Height = 17
      Caption = 'Bi&nary comparison'
      TabOrder = 1
    end
    object RulesBasedEdit: TUiRadioButton
      Left = 8
      Top = 92
      Height = 17
      Caption = 'R&ules-based comparison'
      TabOrder = 2
    end
    object ShowResultsDlgEdit: TUiCheckBox
      Left = 8
      Top = 117
      Height = 17
      Caption = 'Show resul&ts dialog'
      TabOrder = 3
    end
  end
  object FilteredWarnPanel: TUiPanel
    Top = 289
  end
  object BtnPanel: TUiBtnPanel
    Top = 369
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
