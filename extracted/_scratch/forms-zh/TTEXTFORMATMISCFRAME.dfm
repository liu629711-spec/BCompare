object TextFormatMiscFrame: TTextFormatMiscFrame
  HelpType = htKeyword
  HelpKeyword = 'FormatTextMisc'
  Caption = 'Misc'
  object TabSizeLbl: TUiLabel
    Left = 8
    Top = 33
    Height = 13
    Caption = '&Tab stop:'
    FocusControl = TabSizeEdit
  end
  object TabAsSpacesEdit: TUiCheckBox
    Left = 8
    Top = 8
    Height = 17
    Caption = '&Insert spaces instead of tabs'
    TabOrder = 0
    OnClick = SomethingChangedClick
  end
  object TabSizeEdit: TUiSpinEdit
    Left = 8
    Top = 50
    Width = 41
    Height = 21
    Min = 1
    Position = 8
    TabOrder = 1
    OnChange = SomethingChangedClick
  end
  object LineBasedEdit: TUiCheckBox
    Left = 8
    Top = 79
    Height = 17
    Caption = '&Lines are independent'
    TabOrder = 2
    OnClick = SomethingChangedClick
  end
  object ColBasedEdit: TUiCheckBox
    Left = 8
    Top = 100
    Height = 17
    Caption = '&Column-based data'
    TabOrder = 3
    OnClick = SomethingChangedClick
  end
end
