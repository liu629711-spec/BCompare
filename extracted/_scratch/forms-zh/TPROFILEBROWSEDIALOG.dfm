object ProfileBrowseDialog: TProfileBrowseDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgProfileBrowse'
  BorderIcons = [biSystemMenu, biHelp]
  BorderStyle = bsSizeable
  Caption = 'Browse Using Profile'
  ClientHeight = 590
  ClientWidth = 632
  Constraints.MinHeight = 482
  Constraints.MinWidth = 375
  OnActivate = FormActivate
  OnClose = FormClose
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
  object TopPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 632
    Height = 29
    Align = alTop
    BevelOuter = bvNone
    TabOrder = 0
    object SpecFrame: TFormattedSpecFrame
      Left = 8
      Top = 8
      Width = 616
      Height = 16
      TabOrder = 0
      object SpecPreLbl: TUiLabel
        FontStyle = [fsBold]
      end
      object SpecLbl: TUiLabel
        FontStyle = [fsBold]
      end
    end
  end
  object Panel: TUiPanel
    Left = 0
    Top = 29
    Width = 632
    Height = 511
    Align = alClient
    BevelOuter = bvNone
    TabOrder = 1
    object LeftBevel: TUiBevel
      Left = 0
      Top = 0
      Width = 8
      Height = 511
      Align = alLeft
      Shape = bsSpacer
    end
    object Splitter: TUiSplitter
      Left = 192
      Top = 0
      Width = 8
      Height = 511
      OnCanResize = SplitterCanResize
      OnMoved = SplitterMoved
    end
    object ListPanel: TUiPanel
      Left = 8
      Top = 0
      Width = 184
      Height = 511
      Align = alLeft
      BevelOuter = bvNone
      TabOrder = 0
      OnResize = ListPanelResize
      object TreeView: TUiTreeView
        Left = 0
        Top = 0
        Width = 184
        Height = 480
        DragMode = dmAutomatic
        Images = BcImages.MainImages
        PopupMenu = TreePopup
        TabOrder = 0
        OnCancelEdit = TreeViewCancelEdit
        OnChange = TreeViewChange
        OnDblClick = TreeViewDblClick
        OnDragDrop = TreeViewDragDrop
        OnDragOver = TreeViewDragOver
        OnEdited = TreeViewEdited
        OnEditing = TreeViewEditing
        OnKeyDown = TreeViewKeyDown
        OnKeyPress = TreeViewKeyPress
      end
      object NewBtn: TUiBitBtn
        Left = 0
        Top = 488
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
        Top = 488
        Width = 24
        Hint = 'Delete'
        ImageIndex = imgListDelete
        Images = BcImages.MainImages
        TabOrder = 2
        OnClick = DeleteClick
      end
      object EditBtn: TUiBitBtn
        Left = 48
        Top = 488
        Width = 24
        Hint = 'Edit'
        ImageIndex = imgListEdit
        Images = BcImages.MainImages
        TabOrder = 3
        OnClick = EditClick
      end
    end
    object PanelView: TUiActivePanelView
      Left = 200
      Top = 0
      Width = 432
      Height = 511
      Align = alClient
      TabOrder = 1
      object EditPanel: TUiActivePanel
        OnResize = EditPanelResize
        object EditPageControl: TUiPageControl
          Left = 0
          Top = 0
          Width = 424
          Height = 480
          TabOrder = 0
        end
        object EditSaveBtn: TUiButton
          Left = 271
          Top = 488
          Caption = 'Save'
          Default = True
          TabOrder = 1
          OnClick = EditSaveClick
          AutoSize = asRight
        end
        object EditCancelBtn: TUiButton
          Left = 351
          Top = 488
          Cancel = True
          Caption = 'Cancel'
          TabOrder = 2
          OnClick = EditCancelClick
          AutoSize = asRight
        end
      end
      object LocalPanel: TUiActivePanel
        object LocalRightBevel: TUiBevel
          Left = 424
          Top = 0
          Width = 8
          Height = 480
          Align = alRight
          Shape = bsSpacer
        end
        object LocalTreeView: TUiDirectoryTreeView
          Left = 0
          Top = 0
          Width = 424
          Height = 480
          Options = [ptstoDefaultKeyHandling, ptstoContextMenus, ptstoIncludeNonFolders]
          Indent = 19
          OnChange = LocalTreeViewChange
          Align = alClient
          TabOrder = 0
          OnClick = LocalTreeViewClick
          OnEdited = LocalTreeViewEdited
        end
        object LocalBottomPanel: TUiPanel
          Left = 0
          Top = 480
          Width = 432
          Height = 31
          Align = alBottom
          BevelOuter = bvNone
          TabOrder = 1
          object LocalCreateDirBtn: TUiBitBtn
            Left = 0
            Top = 8
            Caption = '&Create New Folder'
            ImageIndex = imgNewFolder
            Images = BcImages.MainImages
            TabOrder = 0
            OnClick = LocalCreateDirClick
            AutoSize = asLeft
          end
        end
      end
      object NamedPanel: TUiActivePanel
        object NamedRightBevel: TUiBevel
          Left = 424
          Top = 0
          Width = 8
          Height = 511
          Align = alRight
          Shape = bsSpacer
        end
        object NamedFrame: TProfileBrowseRemoteFrame
          Left = 0
          Top = 0
          Width = 424
          Height = 511
          Align = alClient
          TabOrder = 0
        end
      end
      object UnnamedPanel: TUiActivePanel
        object UnnamedRightBevel: TUiBevel
          Left = 424
          Top = 0
          Width = 8
          Height = 511
          Align = alRight
          Shape = bsSpacer
        end
      end
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 551
    Width = 632
    TabOrder = 2
    SizeGripper = True
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
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
    object EditItem: TUiMenuItem
      Caption = 'Edit'
      OnClick = EditClick
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
