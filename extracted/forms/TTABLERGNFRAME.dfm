object TableRgnFrame: TTableRgnFrame
  Left = 0
  Top = 0
  Width = 273
  Height = 125
  TabOrder = 0
  object DecimalSeparatorLbl: TUiLabel
    Left = 8
    Top = 33
    Height = 13
    Caption = 'De&cimal separator:'
    FocusControl = DecimalSeparatorEdit
  end
  object ThousandSeparatorLbl: TUiLabel
    Left = 8
    Top = 79
    Height = 13
    Caption = '&Thousands separator:'
    FocusControl = ThousandSeparatorEdit
  end
  object DateOrderLbl: TUiLabel
    Left = 140
    Top = 33
    Height = 13
    Caption = 'Date &order:'
    FocusControl = DateOrderEdit
  end
  object DateSeparatorLbl: TUiLabel
    Left = 140
    Top = 79
    Height = 13
    Caption = 'Date &separator:'
    FocusControl = DateSeparatorEdit
  end
  object UseSystemEdit: TUiCheckBox
    Left = 8
    Top = 8
    Height = 17
    Caption = 'Use s&ystem'
    TabOrder = 0
    OnClick = SomethingChangedClick
  end
  object DecimalSeparatorEdit: TUiCharEdit
    Left = 8
    Top = 50
    Width = 17
    Height = 21
    TabOrder = 1
    OnChange = SomethingChangedClick
  end
  object ThousandSeparatorEdit: TUiCharEdit
    Left = 8
    Top = 96
    Width = 17
    Height = 21
    TabOrder = 2
    OnChange = SomethingChangedClick
  end
  object DateOrderEdit: TUiComboBox
    Left = 140
    Top = 50
    Width = 67
    Height = 21
    Style = csDropDownList
    TabOrder = 3
    OnChange = SomethingChangedClick
  end
  object DateSeparatorEdit: TUiCharEdit
    Left = 140
    Top = 96
    Width = 17
    Height = 21
    TabOrder = 4
    OnChange = SomethingChangedClick
  end
end
