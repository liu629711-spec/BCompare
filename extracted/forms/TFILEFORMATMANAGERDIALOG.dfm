object FileFormatManagerDialog: TFileFormatManagerDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgFileFormatManager'
  BorderIcons = [biSystemMenu, biHelp]
  BorderStyle = bsSizeable
  Caption = 'File Formats'
  ClientHeight = 590
  ClientWidth = 672
  Constraints.MinHeight = 473
  Constraints.MinWidth = 417
  OnActivate = FormActivate
  OnCloseQuery = FormCloseQuery
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnResize = FormResize
  OnShortCut = FormShortCut
  PixelsPerInch = 96
  TextHeight = 13
  object BottomLineBevel: TUiBevel
    Left = 0
    Top = 540
    Width = 672
    Height = 11
    Align = alBottom
    Shape = bsBottomLine
  end
  object Panel: TUiPanel
    Left = 0
    Top = 0
    Width = 672
    Height = 540
    Align = alClient
    BevelOuter = bvNone
    TabOrder = 0
    object TopBevel: TUiBevel
      Left = 0
      Top = 0
      Width = 672
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
      Left = 232
      Top = 8
      Width = 8
      Height = 532
      OnCanResize = SplitterCanResize
      OnMoved = SplitterMoved
    end
    object ListPanel: TUiPanel
      Left = 8
      Top = 8
      Width = 224
      Height = 532
      Align = alLeft
      BevelOuter = bvNone
      TabOrder = 0
      OnResize = ListPanelResize
      object ListViewPanel: TUiPanel
        Left = 0
        Top = 0
        Width = 224
        Height = 501
        BevelOuter = bvNone
        TabOrder = 0
        object ListView: TUiListView
          Left = 0
          Top = 0
          Width = 224
          Height = 501
          Align = alClient
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
          DragMode = dmAutomatic
          RowSelect = True
          PopupMenu = ListPopup
          SmallImages = BcImages.MainImages
          TabOrder = 0
          ViewStyle = vsReport
          OnCustomDrawItem = ListViewCustomDrawItem
          OnCustomDrawSubItem = ListViewCustomDrawSubItem
          OnEdited = ListViewEdited
          OnEditing = ListViewEditing
          OnDragDrop = ListViewDragDrop
          OnDragOver = ListViewDragOver
          OnKeyDown = ListViewKeyDown
          OnSelectItem = ListViewSelectItem
          OnCancelEdit = ListViewCancelEdit
          OnCanCheck = ListViewCanCheck
          OnChecked = ListViewChecked
        end
      end
      object NewBtn: TUiBitBtn
        Left = 0
        Top = 509
        Width = 24
        Hint = 'New'
        ImageIndex = imgListAdd
        Images = BcImages.MainImages
        TabOrder = 1
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
      object MoveUpBtn: TUiBitBtn
        Left = 48
        Top = 509
        Width = 24
        Hint = 'Move Up'
        ImageIndex = imgUp
        Images = BcImages.MainImages
        TabOrder = 3
        OnClick = MoveUpClick
      end
      object MoveDownBtn: TUiBitBtn
        Left = 72
        Top = 509
        Width = 24
        Hint = 'Move Down'
        ImageIndex = imgDown
        Images = BcImages.MainImages
        TabOrder = 4
        OnClick = MoveDownClick
      end
    end
    object EditPanel: TUiPanel
      Left = 240
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
      object EditResBtn: TUiButton
        Left = 0
        Top = 509
        Caption = 'Factory &Defaults'
        TabOrder = 1
        OnClick = EditResClick
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
    Width = 672
    TabOrder = 1
    SizeGripper = True
    object LinkLbl: TUiLinkLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'Additional file formats available on <a href="%s">Scooter Software''s web site</a>.'
    end
    object CloseBtn: TUiCloseBtn
    end
  end
  object ListPopup: TUiPopupMenu
    Left = 8
    Top = 8
    object NewListItem: TUiSubmenuItem
      Caption = 'New'
      OnClick = NewListClick
    end
    object MoveUpItem: TUiMenuItem
      Caption = 'Move Up'
      ShortCut = 16422
      OnClick = MoveUpClick
    end
    object MoveDownItem: TUiMenuItem
      Caption = 'Move Down'
      ShortCut = 16424
      OnClick = MoveDownClick
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
  end
  object NewPopup: TUiPopupMenu
    Images = BcImages.MainImages
    OnPopup = NewListClick
    Left = 40
    Top = 8
  end
end
