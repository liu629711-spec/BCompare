object TableSortItemFrame: TTableSortItemFrame
  Left = 0
  Top = 0
  Width = 200
  Height = 54
  TabOrder = 0
  object Bevel: TUiBevel
    Left = 8
    Top = 0
    Width = 184
    Height = 1
    Shape = bsTopLine
  end
  object ColLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Then by:'
  end
  object ColEdit: TUiComboBox
    Left = 8
    Top = 25
    Width = 120
    Height = 21
    Style = csDropDownList
    TabOrder = 0
  end
  object UpEdit: TUiRadioButton
    Left = 136
    Top = 8
    Height = 17
    Caption = 'A --> Z'
    TabOrder = 1
  end
  object DownEdit: TUiRadioButton
    Left = 136
    Top = 29
    Height = 17
    Caption = 'Z --> A'
    TabOrder = 2
  end
end
