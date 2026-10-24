object TableSessionColumnsFrame: TTableSessionColumnsFrame
  HelpType = htKeyword
  HelpKeyword = 'SessionTableColumns'
  Caption = 'Columns'
  object SheetLbl: TUiLabel
    Left = 316
    Top = 12
    Height = 13
    Caption = 'S&heet:'
    FocusControl = SheetEdit
  end
  object KindEdit: TUiComboBox
    Left = 8
    Top = 8
    Width = 121
    Height = 21
    Style = csDropDownList
    TabOrder = 0
    OnChange = KindEditChange
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
  object Editor: TUiVirtualTableView
    Left = 8
    Top = 33
    Width = 409
    Height = 288
    AlphaItemNum = True
    GutterImages = BcImages.HeaderImages
    PopupMenu = Popup
    TabOrder = 2
    OnChanged = EditorChanged
    OnColDetectSize = EditorColDetectSize
    OnDblClick = EditClick
    OnDrawCellPrep = EditorDrawCellPrep
    OnGetCellStr = EditorGetCellStr
    OnGetColName = EditorGetColName
    OnGetColWidth = EditorGetColWidth
    OnGetGutterImageIndex = EditorGetGutterImageIndex
    OnGetItemNum = EditorGetItemNum
    OnKeyDown = EditorKeyDown
    OnSetColWidth = EditorSetColWidth
  end
  object EditBtn: TUiBitBtn
    Left = 8
    Top = 329
    Width = 24
    Hint = 'Edit'
    ImageIndex = imgListEdit
    Images = BcImages.MainImages
    TabOrder = 3
    OnClick = EditClick
  end
  object MoveUpBtn: TUiBitBtn
    Left = 32
    Top = 329
    Width = 24
    Hint = 'Move Up'
    ImageIndex = imgUp
    Images = BcImages.MainImages
    TabOrder = 4
    OnClick = MoveUpClick
  end
  object MoveDownBtn: TUiBitBtn
    Left = 56
    Top = 329
    Width = 24
    Hint = 'Move Down'
    ImageIndex = imgDown
    Images = BcImages.MainImages
    TabOrder = 5
    OnClick = MoveDownClick
  end
  object EditDefaultBtn: TUiButton
    Left = 296
    Top = 329
    Width = 84
    Caption = '&Edit Default...'
    TabOrder = 6
    OnClick = EditDefaultClick
    AutoSize = asRight
    AutoSizeMinWidth = 0
  end
  object TidyBtn: TUiButton
    Left = 381
    Top = 329
    Width = 36
    Caption = '&Tidy'
    TabOrder = 7
    OnClick = TidyClick
    AutoSize = asRight
    AutoSizeMinWidth = 0
  end
  object Popup: TUiPopupMenu
    OnPopup = ListClick
    Left = 8
    Top = 8
  end
end
