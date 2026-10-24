object TextFormatGrammarFrame: TTextFormatGrammarFrame
  HelpType = htKeyword
  HelpKeyword = 'FormatTextGrammar'
  Caption = 'Grammar'
  object WeightsLbl: TUiLabel
    Left = 8
    Top = 192
    Height = 13
    Caption = 'Line &weights:'
    FocusControl = WeightsTable
  end
  object GrammarListBox: TUiListBox
    Left = 8
    Top = 8
    Width = 257
    Height = 145
    DragMode = dmAutomatic
    ParentShowHint = False
    ShowHint = False
    TabOrder = 0
    OnClick = GrammarListBoxClick
    OnDblClick = GrammarEditClick
    OnDragDrop = GrammarListBoxDragDrop
    OnDragOver = GrammarListBoxDragOver
    OnKeyDown = GrammarListBoxKeyDown
  end
  object GrammarNewBtn: TUiBitBtn
    Left = 8
    Top = 161
    Width = 24
    Hint = 'New'
    ImageIndex = imgListAdd
    Images = BcImages.MainImages
    TabOrder = 1
    OnClick = GrammarNewClick
  end
  object GrammarDeleteBtn: TUiBitBtn
    Left = 32
    Top = 161
    Width = 24
    Hint = 'Delete'
    ImageIndex = imgListDelete
    Images = BcImages.MainImages
    TabOrder = 2
    OnClick = GrammarDeleteClick
  end
  object GrammarEditBtn: TUiBitBtn
    Left = 56
    Top = 161
    Width = 24
    Hint = 'Edit'
    ImageIndex = imgListEdit
    Images = BcImages.MainImages
    TabOrder = 3
    OnClick = GrammarEditClick
  end
  object GrammarCloneBtn: TUiBitBtn
    Left = 80
    Top = 161
    Width = 24
    Hint = 'Clone'
    ImageIndex = imgListClone
    Images = BcImages.MainImages
    TabOrder = 4
    OnClick = GrammarCloneClick
  end
  object GrammarMoveUpBtn: TUiBitBtn
    Left = 104
    Top = 161
    Width = 24
    Hint = 'Move Up'
    ImageIndex = imgUp
    Images = BcImages.MainImages
    TabOrder = 5
    OnClick = GrammarMoveUpClick
  end
  object GrammarMoveDownBtn: TUiBitBtn
    Left = 128
    Top = 161
    Width = 24
    Hint = 'Move Down'
    ImageIndex = imgDown
    Images = BcImages.MainImages
    TabOrder = 6
    OnClick = GrammarMoveDownClick
  end
  object WeightsTable: TUiListTable
    Left = 8
    Top = 209
    Width = 257
    Height = 73
    Cols.Data = ('', '64')
    Cols.Strings = ('Text matching', 'Priority')
    DeleteItemQueryDefault = True
    DragMode = dmAutomatic
    TabOrder = 7
    VertLines = True
    WantReturns = True
    OnAddItem = WeightsNewClick
    OnDblClick = WeightsEditClick
    OnDeleteItem = WeightsTableDeleteItem
    OnDragDrop = WeightsTableDragDrop
    OnDragOver = WeightsTableDragOver
    OnGetCells = WeightsTableGetCells
    OnItemsDeleted = SomethingChangedClick
    OnKeyDown = WeightsTableKeyDown
  end
  object WeightsNewBtn: TUiBitBtn
    Left = 8
    Top = 290
    Width = 24
    Hint = 'New'
    ImageIndex = imgListAdd
    Images = BcImages.MainImages
    TabOrder = 8
    OnClick = WeightsNewClick
  end
  object WeightsDeleteBtn: TUiBitBtn
    Left = 32
    Top = 290
    Width = 24
    Hint = 'Delete'
    ImageIndex = imgListDelete
    Images = BcImages.MainImages
    TabOrder = 9
    OnClick = WeightsDeleteClick
  end
  object WeightsEditBtn: TUiBitBtn
    Left = 56
    Top = 290
    Width = 24
    Hint = 'Edit'
    ImageIndex = imgListEdit
    Images = BcImages.MainImages
    TabOrder = 10
    OnClick = WeightsEditClick
  end
end
