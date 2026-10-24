object LineAlignDefFrame: TLineAlignDefFrame
  Left = 0
  Top = 0
  Width = 425
  Height = 104
  TabOrder = 0
  object SkewToleranceLbl: TUiLabel
    Left = 216
    Top = 33
    Height = 13
    Caption = 'Ske&w tolerance:'
    FocusControl = SkewToleranceEdit
  end
  object SkewToleranceDescLbl: TUiLabel
    Left = 277
    Top = 54
    Height = 13
    Caption = 'lines (default 2000)'
  end
  object AlignNoneEdit: TUiRadioButton
    Left = 8
    Top = 8
    Height = 17
    Caption = '&Unaligned'
    TabOrder = 0
    OnClick = SomethingChangedClick
  end
  object AlignSmartEdit: TUiRadioButton
    Left = 8
    Top = 29
    Height = 17
    Caption = 'Standa&rd alignment'
    TabOrder = 1
    OnClick = SomethingChangedClick
  end
  object AlignQuickEdit: TUiRadioButton
    Left = 8
    Top = 50
    Height = 17
    Caption = '&Myers O(ND) alignment'
    TabOrder = 2
    OnClick = SomethingChangedClick
  end
  object AlignPatienceEdit: TUiRadioButton
    Left = 8
    Top = 71
    Height = 17
    Caption = '&Patience Diff alignment'
    TabOrder = 3
    OnClick = SomethingChangedClick
  end
  object NeverAlignDiffsEdit: TUiCheckBox
    Left = 216
    Top = 8
    Height = 17
    Caption = '&Never align differences'
    TabOrder = 4
    OnClick = NeverAlignDiffsClick
  end
  object SkewToleranceEdit: TUiSpinEdit
    Left = 216
    Top = 50
    Width = 57
    Height = 21
    Increment = 50
    Max = 30000
    MaxLength = 5
    Min = 1
    Position = 2000
    TabOrder = 5
    OnChange = SomethingChangedClick
  end
  object UseClosenessEdit: TUiCheckBox
    Left = 216
    Top = 79
    Height = 17
    Caption = 'Use &closeness matching'
    TabOrder = 6
    OnClick = UseClosenessClick
  end
end
