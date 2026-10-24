object DirSessionOtherFiltersFrame: TDirSessionOtherFiltersFrame
  HelpType = htKeyword
  HelpKeyword = 'SessionDirOtherFilters'
  Caption = 'Other Filters'
  object OtherFiltersListBox: TUiListBox
    Left = 8
    Top = 8
    Width = 409
    Height = 288
    DragMode = dmAutomatic
    TabOrder = 0
    OnClick = OtherFiltersListBoxClick
    OnDblClick = OtherFiltersEditClick
    OnDragDrop = OtherFiltersListBoxDragDrop
    OnDragOver = OtherFiltersListBoxDragOver
    OnKeyDown = OtherFiltersListBoxKeyDown
  end
  object OtherFiltersNewBtn: TUiBitBtn
    Left = 8
    Top = 304
    Width = 24
    Hint = 'New'
    ImageIndex = imgListAdd
    Images = BcImages.MainImages
    TabOrder = 1
    OnClick = OtherFiltersNewClick
  end
  object OtherFiltersDeleteBtn: TUiBitBtn
    Left = 32
    Top = 304
    Width = 24
    Hint = 'Delete'
    ImageIndex = imgListDelete
    Images = BcImages.MainImages
    TabOrder = 2
    OnClick = OtherFiltersDeleteClick
  end
  object OtherFiltersEditBtn: TUiBitBtn
    Left = 56
    Top = 304
    Width = 24
    Hint = 'Edit'
    ImageIndex = imgListEdit
    Images = BcImages.MainImages
    TabOrder = 3
    OnClick = OtherFiltersEditClick
  end
  object OtherFiltersCloneBtn: TUiBitBtn
    Left = 80
    Top = 304
    Width = 24
    Hint = 'Clone'
    ImageIndex = imgListClone
    Images = BcImages.MainImages
    TabOrder = 4
    OnClick = OtherFiltersCloneClick
  end
  object ExcludeHiddenSystemEdit: TUiCheckBox
    Left = 8
    Top = 335
    Height = 17
    Caption = 'Exclude protected operating s&ystem files (Recommended)'
    TabOrder = 5
    OnClick = SomethingChangedClick
  end
end
