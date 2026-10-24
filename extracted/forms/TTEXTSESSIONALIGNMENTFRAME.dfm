object TextSessionAlignmentFrame: TTextSessionAlignmentFrame
  HelpType = htKeyword
  HelpKeyword = 'SessionTextAlignment'
  Caption = 'Alignment'
  object Frame: TLineAlignDefFrame
    Left = 0
    Top = 0
    Width = 425
    Height = 104
    TabOrder = 0
  end
  object ConflictScanLinesPanel: TUiPanel
    Left = 0
    Top = 104
    Width = 425
    Height = 96
    BevelOuter = bvNone
    TabOrder = 1
    object ConflictScanLinesBevel: TUiBevel
      Left = 8
      Top = 0
      Width = 409
      Height = 1
      Shape = bsTopLine
    end
    object ConflictScanLinesLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'A merge conflict is:'
    end
    object ConflictScanLinesNegEdit: TUiRadioButton
      Left = 8
      Top = 25
      Height = 17
      Caption = '&Only different change lines'
      TabOrder = 0
      OnClick = SomethingChangedClick
    end
    object ConflictScanLinesOtherEdit: TUiRadioButton
      Left = 8
      Top = 46
      Height = 17
      Caption = '&Left change and right change separated by lines:'
      TabOrder = 1
      OnClick = SomethingChangedClick
    end
    object ConflictScanLinesEdit: TUiSpinEdit
      Left = 24
      Top = 67
      Width = 41
      Height = 21
      Max = 256
      MaxLength = 3
      Position = 1
      TabOrder = 2
      OnChange = SomethingChangedClick
    end
  end
end
