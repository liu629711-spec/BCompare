object DirSessionMiscFrame: TDirSessionMiscFrame
  HelpType = htKeyword
  HelpKeyword = 'SessionDirMisc'
  Caption = 'Misc'
  object AlignWithsLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Ali&gnment overrides:'
    FocusControl = AlignWithsTable
  end
  object FileFormatLbl: TUiLabel
    Left = 8
    Top = 184
    Height = 13
    Caption = 'Enabled &file formats:'
    FocusControl = FileFormatListView
  end
  object AlignWithsTable: TUiListTable
    Left = 8
    Top = 25
    Width = 409
    Height = 120
    Cols.Data = ('', '20', '')
    Cols.Strings = ('Left', '', 'Right')
    DeleteItemQueryDefault = True
    DragMode = dmAutomatic
    ImageColIndex = 1
    Images = BcImages.MainImages
    TabOrder = 0
    OnAddItem = AlignWithsNewClick
    OnClick = AlignWithsTableClick
    OnDblClick = AlignWithsEditClick
    OnDeleteItem = AlignWithsTableDeleteItem
    OnDragDrop = AlignWithsTableDragDrop
    OnDragOver = AlignWithsTableDragOver
    OnGetCells = AlignWithsTableGetCells
    OnGetImageIndex = AlignWithsTableGetImageIndex
    OnItemsDeleted = SomethingChangedClick
    OnKeyDown = AlignWithsTableKeyDown
  end
  object AlignWithsNewBtn: TUiBitBtn
    Left = 8
    Top = 153
    Width = 24
    Hint = 'New'
    ImageIndex = imgListAdd
    Images = BcImages.MainImages
    TabOrder = 1
    OnClick = AlignWithsNewClick
  end
  object AlignWithsDeleteBtn: TUiBitBtn
    Left = 32
    Top = 153
    Width = 24
    Hint = 'Delete'
    ImageIndex = imgListDelete
    Images = BcImages.MainImages
    TabOrder = 2
    OnClick = AlignWithsDeleteClick
  end
  object AlignWithsEditBtn: TUiBitBtn
    Left = 56
    Top = 153
    Width = 24
    Hint = 'Edit'
    ImageIndex = imgListEdit
    Images = BcImages.MainImages
    TabOrder = 3
    OnClick = AlignWithsEditClick
  end
  object AlignWithsCloneBtn: TUiBitBtn
    Left = 80
    Top = 153
    Width = 24
    Hint = 'Clone'
    ImageIndex = imgListClone
    Images = BcImages.MainImages
    TabOrder = 4
    OnClick = AlignWithsCloneClick
  end
  object FileFormatListView: TUiListView
    Left = 8
    Top = 201
    Width = 409
    Height = 151
    Checkboxes = True
    Columns = <
      item
        AutoSize = True
      end
      item
        AutoSize = True
      end
    >
    ColumnClick = False
    ReadOnly = True
    RowSelect = True
    PopupMenu = FileFormatPopup
    SmallImages = BcImages.MainImages
    TabOrder = 5
    ViewStyle = vsReport
    OnClick = FileFormatListViewClick
    OnCustomDrawItem = FileFormatListViewCustomDrawItem
    OnDblClick = FileFormatEditClick
    OnCancelEdit = FileFormatListViewCancelEdit
    OnCanCheck = FileFormatListViewCanCheck
    OnChecked = FileFormatListViewChecked
  end
  object FileFormatPopup: TUiPopupMenu
    Left = 8
    Top = 8
    object FileFormatEditItem: TUiMenuItem
      Caption = 'Edit...'
      OnClick = FileFormatEditClick
    end
    object FileFormatSeparatorItem: TUiSeparatorItem
    end
    object FileFormatAllItem: TUiMenuItem
      Caption = 'Mark All'
      OnClick = FileFormatCheckedClick
    end
    object FileFormatNoneItem: TUiMenuItem
      Caption = 'Unmark All'
      OnClick = FileFormatCheckedClick
    end
  end
end
