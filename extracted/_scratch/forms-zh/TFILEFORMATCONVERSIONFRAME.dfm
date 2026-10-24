object FileFormatConversionFrame: TFileFormatConversionFrame
  HelpType = htKeyword
  Caption = 'Conversion'
  object ConvertLoadAppLbl: TUiLabel
    Left = 24
    Top = 33
    Height = 13
    Caption = '&Loading:'
    FocusControl = ConvertLoadAppEdit
  end
  object ConvertKindEdit: TUiComboBox
    Left = 8
    Top = 8
    Width = 257
    Height = 21
    Style = csDropDownList
    TabOrder = 0
    OnChange = ConvertKindEditChange
  end
  object ConvertLoadAppEdit: TUiSpecBar
    Left = 24
    Top = 50
    Width = 241
    TabOrder = 1
    OnBrowse = ConvertAppEditBrowse
    OnChange = SomethingChangedClick
    OnGetArgs = ConvertAppEditGetArgs
  end
end
