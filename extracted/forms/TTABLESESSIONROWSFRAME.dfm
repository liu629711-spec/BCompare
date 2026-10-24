object TableSessionRowsFrame: TTableSessionRowsFrame
  HelpType = htKeyword
  HelpKeyword = 'SessionTableRows'
  Caption = 'Rows'
  object SheetLbl: TUiLabel
    Left = 316
    Top = 12
    Height = 13
    Caption = 'S&heet:'
    FocusControl = SheetEdit
  end
  object KeyLbl: TUiLabel
    Left = 8
    Top = 162
    Height = 13
    Caption = 'Key columns are defined.  Key based alignment will be used.'
    FontStyle = [fsBold]
  end
  object UseDefaultEdit: TUiCheckBox
    Left = 8
    Top = 8
    Height = 17
    Caption = 'Use de&fault'
    TabOrder = 0
    OnClick = UseDefaultClick
  end
  object SheetEdit: TUiComboBox
    Left = 352
    Top = 8
    Width = 65
    Height = 21
    Style = csDropDownList
    TabOrder = 1
    OnChange = SheetEditChange
  end
  object Frame: TLineAlignDefFrame
    Left = 0
    Top = 33
    Width = 425
    Height = 104
    TabOrder = 2
  end
  object AlignSortEdit: TUiCheckBox
    Left = 8
    Top = 137
    Height = 17
    Caption = 'S&ort rows before alignment'
    TabOrder = 3
    OnClick = AlignSortClick
  end
  object EditDefaultBtn: TUiButton
    Left = 333
    Top = 329
    Width = 84
    Caption = '&Edit Default...'
    TabOrder = 4
    OnClick = EditDefaultClick
    AutoSize = asRight
    AutoSizeMinWidth = 0
  end
end
