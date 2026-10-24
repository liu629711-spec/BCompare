object PixSessionReplacementsFrame: TPixSessionReplacementsFrame
  HelpType = htKeyword
  HelpKeyword = 'SessionPixReplacements'
  Caption = 'Replacements'
  object ReplacementsTable: TUiListTable
    Left = 8
    Top = 8
    Width = 409
    Height = 313
    Cols.Data = ('', '20', '')
    Cols.Strings = ('Left', '', 'Right')
    DeleteItemQueryDefault = True
    DragMode = dmAutomatic
    ImageColIndex = 1
    Images = BcImages.MainImages
    TabOrder = 0
    OnAddItem = ReplacementsNewClick
    OnClick = ReplacementsTableClick
    OnDblClick = ReplacementsEditClick
    OnDeleteItem = ReplacementsTableDeleteItem
    OnDragDrop = ReplacementsTableDragDrop
    OnDragOver = ReplacementsTableDragOver
    OnGetCells = ReplacementsTableGetCells
    OnGetImageIndex = ReplacementsTableGetImageIndex
    OnItemsDeleted = SomethingChangedClick
    OnKeyDown = ReplacementsTableKeyDown
  end
  object ReplacementsNewBtn: TUiBitBtn
    Left = 8
    Top = 329
    Width = 24
    Hint = 'New'
    ImageIndex = imgListAdd
    Images = BcImages.MainImages
    TabOrder = 1
    OnClick = ReplacementsNewClick
  end
  object ReplacementsDeleteBtn: TUiBitBtn
    Left = 32
    Top = 329
    Width = 24
    Hint = 'Delete'
    ImageIndex = imgListDelete
    Images = BcImages.MainImages
    TabOrder = 2
    OnClick = ReplacementsDeleteClick
  end
  object ReplacementsEditBtn: TUiBitBtn
    Left = 56
    Top = 329
    Width = 24
    Hint = 'Edit'
    ImageIndex = imgListEdit
    Images = BcImages.MainImages
    TabOrder = 3
    OnClick = ReplacementsEditClick
  end
  object ReplacementsCloneBtn: TUiBitBtn
    Left = 80
    Top = 329
    Width = 24
    Hint = 'Clone'
    ImageIndex = imgListClone
    Images = BcImages.MainImages
    TabOrder = 4
    OnClick = ReplacementsCloneClick
  end
end
