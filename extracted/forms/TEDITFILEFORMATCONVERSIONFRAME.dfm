object EditFileFormatConversionFrame: TEditFileFormatConversionFrame
  object ConvertSaveAppLbl: TUiLabel
    Left = 24
    Top = 96
    Height = 13
    Caption = 'Sa&ving:'
    FocusControl = ConvertSaveAppEdit
  end
  object ConvertNoEditEdit: TUiCheckBox
    Left = 24
    Top = 75
    Height = 17
    Caption = 'D&isable editing'
    TabOrder = 2
    OnClick = SomethingChangedClick
  end
  object ConvertSaveAppEdit: TUiSpecBar
    Left = 24
    Top = 113
    Width = 241
    TabOrder = 3
    OnBrowse = ConvertAppEditBrowse
    OnChange = SomethingChangedClick
    OnGetArgs = ConvertAppEditGetArgs
  end
end
