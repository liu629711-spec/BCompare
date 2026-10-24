object TableSessionSheetsFrame: TTableSessionSheetsFrame
  HelpType = htKeyword
  HelpKeyword = 'SessionTableSheets'
  Caption = 'Sheets'
  object KindEdit: TUiComboBox
    Left = 8
    Top = 8
    Width = 121
    Height = 21
    Style = csDropDownList
    TabOrder = 0
    OnChange = KindEditChange
  end
  object Editor: TUiVirtualTableView
    Left = 8
    Top = 33
    Width = 409
    Height = 288
    GutterImages = BcImages.HeaderImages
    TabOrder = 1
    OnChanged = EditorChanged
    OnColDetectSize = EditorColDetectSize
    OnDrawCellPrep = EditorDrawCellPrep
    OnGetCellStr = EditorGetCellStr
    OnGetColName = EditorGetColName
    OnGetColWidth = EditorGetColWidth
    OnGetItemNum = EditorGetItemNum
    OnKeyDown = EditorKeyDown
    OnSetColWidth = EditorSetColWidth
  end
  object MoveUpBtn: TUiBitBtn
    Left = 8
    Top = 329
    Width = 24
    Hint = 'Move Up'
    ImageIndex = imgUp
    Images = BcImages.MainImages
    TabOrder = 2
    OnClick = MoveUpClick
  end
  object MoveDownBtn: TUiBitBtn
    Left = 32
    Top = 329
    Width = 24
    Hint = 'Move Down'
    ImageIndex = imgDown
    Images = BcImages.MainImages
    TabOrder = 3
    OnClick = MoveDownClick
  end
  object TidyBtn: TUiButton
    Left = 381
    Top = 329
    Width = 36
    Caption = '&Tidy'
    TabOrder = 4
    OnClick = TidyClick
    AutoSize = asRight
    AutoSizeMinWidth = 0
  end
end
