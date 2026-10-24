object ProfileManagerDialog: TProfileManagerDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgProfileManager'
  BorderIcons = [biSystemMenu, biHelp]
  BorderStyle = bsSizeable
  Caption = 'Profiles'
  ClientHeight = 590
  ClientWidth = 632
  Constraints.MinHeight = 461
  Constraints.MinWidth = 351
  OnActivate = FormActivate
  OnCloseQuery = FormCloseQuery
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnResize = FormResize
  OnShortCut = FormShortCut
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object BottomLineBevel: TUiBevel
    Left = 0
    Top = 540
    Width = 632
    Height = 11
    Align = alBottom
    Shape = bsBottomLine
  end
  object Panel: TUiPanel
    Left = 0
    Top = 0
    Width = 632
    Height = 540
    Align = alClient
    BevelOuter = bvNone
    TabOrder = 0
    object TopBevel: TUiBevel
      Left = 0
      Top = 0
      Width = 632
      Height = 8
      Align = alTop
      Shape = bsSpacer
    end
    object LeftBevel: TUiBevel
      Left = 0
      Top = 8
      Width = 8
      Height = 532
      Align = alLeft
      Shape = bsSpacer
    end
    object Splitter: TUiSplitter
      Left = 192
      Top = 8
      Width = 8
      Height = 532
      OnCanResize = SplitterCanResize
      OnMoved = SplitterMoved
    end
    object ListPanel: TUiPanel
      Left = 8
      Top = 8
      Width = 184
      Height = 532
      Align = alLeft
      BevelOuter = bvNone
      TabOrder = 0
      OnResize = ListPanelResize
      object TreeView: TUiTreeView
        Left = 0
        Top = 0
        Width = 184
        Height = 501
        DragMode = dmAutomatic
        Images = BcImages.MainImages
        MultiSelect = True
        MultiSelectStyle = [msControlSelect, msShiftSelect, msVisibleOnly]
        PopupMenu = TreePopup
        TabOrder = 0
        OnCancelEdit = TreeViewCancelEdit
        OnChange = TreeViewChange
        OnDragDrop = TreeViewDragDrop
        OnDragOver = TreeViewDragOver
        OnEdited = TreeViewEdited
        OnEditing = TreeViewEditing
        OnKeyDown = TreeViewKeyDown
        OnKeyPress = TreeViewKeyPress
        AllowUnselected = True
      end
      object NewBtn: TUiBitBtn
        Left = 0
        Top = 509
        Width = 24
        Hint = 'New'
        ImageIndex = imgListAdd
        Images = BcImages.MainImages
        PopupMenu = NewPopup
        TabOrder = 1
        DropDownOnClick = True
      end
      object DeleteBtn: TUiBitBtn
        Left = 24
        Top = 509
        Width = 24
        Hint = 'Delete'
        ImageIndex = imgListDelete
        Images = BcImages.MainImages
        TabOrder = 2
        OnClick = DeleteClick
      end
    end
    object EditPanel: TUiPanel
      Left = 200
      Top = 8
      Width = 432
      Height = 532
      Align = alClient
      BevelOuter = bvNone
      TabOrder = 1
      OnResize = EditPanelResize
      object EditPageControl: TUiPageControl
        Left = 0
        Top = 0
        Width = 424
        Height = 501
        TabOrder = 0
      end
      object EditDefaultBtn: TUiButton
        Left = 0
        Top = 509
        Caption = 'Factory &Defaults'
        TabOrder = 1
        OnClick = EditDefaultClick
        AutoSize = asLeft
      end
      object EditSaveBtn: TUiButton
        Left = 191
        Top = 509
        Caption = 'Save'
        Default = True
        TabOrder = 2
        OnClick = EditSaveClick
        AutoSize = asRight
      end
      object EditSaveAsBtn: TUiButton
        Left = 271
        Top = 509
        Caption = 'Save &As...'
        TabOrder = 3
        OnClick = EditSaveAsClick
        AutoSize = asRight
      end
      object EditCancelBtn: TUiButton
        Left = 351
        Top = 509
        Cancel = True
        Caption = 'Cancel'
        TabOrder = 4
        OnClick = EditCancelClick
        AutoSize = asRight
      end
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 551
    Width = 632
    TabOrder = 1
    SizeGripper = True
    object CloseBtn: TUiCloseBtn
    end
  end
  object TreePopup: TUiPopupMenu
    Left = 8
    Top = 8
    object NewListItem: TUiSubmenuItem
      Caption = 'New'
      OnClick = NewListClick
    end
    object DeleteItem: TUiMenuItem
      Caption = 'Delete'
      ShortCut = 46
      OnClick = DeleteClick
    end
    object RenameItem: TUiMenuItem
      Caption = 'Rename'
      ShortCut = 113
      OnClick = RenameClick
    end
    object SeparatorItem: TUiSeparatorItem
    end
    object ExpandAllItem: TUiMenuItem
      Caption = 'Expand All'
      OnClick = ExpandAllClick
    end
    object CollapseAllItem: TUiMenuItem
      Caption = 'Collapse All'
      OnClick = CollapseAllClick
    end
  end
  object NewPopup: TUiPopupMenu
    Images = BcImages.MainImages
    OnPopup = NewListClick
    Left = 40
    Top = 8
  end
end
