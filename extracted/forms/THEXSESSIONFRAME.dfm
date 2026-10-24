object HexSessionFrame: THexSessionFrame
  HelpType = htKeyword
  HelpKeyword = 'SessionHexComparison'
  Caption = 'Comparison'
  object AlignKindLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Alignment:'
  end
  object InMemoryLimitLbl: TUiLabel
    Left = 8
    Top = 92
    Height = 13
    Caption = 'Fi&les up to this size are loaded without file locks:'
    FocusControl = InMemoryLimitEdit
  end
  object InMemoryLimitMBLbl: TUiLabel
    Left = 64
    Top = 113
    Height = 13
    Caption = 'MB'
    FocusControl = InMemoryLimitEdit
  end
  object AlignNoneEdit: TUiRadioButton
    Left = 8
    Top = 25
    Height = 17
    Caption = '&None'
    TabOrder = 0
    OnClick = SomethingChangedClick
  end
  object AlignFastEdit: TUiRadioButton
    Left = 8
    Top = 46
    Height = 17
    Caption = '&Fast'
    TabOrder = 1
    OnClick = SomethingChangedClick
  end
  object AlignCompleteEdit: TUiRadioButton
    Left = 8
    Top = 67
    Height = 17
    Caption = '&Complete'
    TabOrder = 2
    OnClick = SomethingChangedClick
  end
  object InMemoryLimitEdit: TUiSpinEdit
    Left = 8
    Top = 109
    Width = 50
    Height = 21
    Max = 32
    MaxLength = 2
    TabOrder = 3
    OnChange = SomethingChangedClick
  end
end
