object TextFormatConversionFrame: TTextFormatConversionFrame
  HelpKeyword = 'FormatTextConversion'
  object CharPerLineLbl: TUiLabel
    Left = 101
    Top = 233
    Height = 13
    Caption = 'c&haracters per line limit'
    FocusControl = CharPerLineEdit
  end
  object ConvertOnSaveLbl: TUiLabel
    Left = 8
    Top = 258
    Height = 13
    Caption = 'When saving:'
  end
  object CharPerLineEdit: TUiSpinEdit
    Left = 8
    Top = 229
    Width = 89
    Height = 21
    Min = 1
    Position = 1
    TabOrder = 6
    OnChange = SomethingChangedClick
  end
  object TrimTrailingWSEdit: TUiCheckBox
    Left = 8
    Top = 275
    Height = 17
    Caption = '&Trim trailing whitespace'
    TabOrder = 7
    OnClick = SomethingChangedClick
  end
  object TidyLeadingWSEdit: TUiCheckBox
    Left = 8
    Top = 296
    Height = 17
    Caption = 'C&onvert leading spaces to tabs'
    TabOrder = 8
    OnClick = SomethingChangedClick
  end
end
