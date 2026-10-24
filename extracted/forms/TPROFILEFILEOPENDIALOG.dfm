object ProfileFileOpenDialog: TProfileFileOpenDialog
  BorderStyle = bsSizeable
  Caption = 'Open File Using Profile'
  ClientHeight = 371
  ClientWidth = 362
  Constraints.MinHeight = 190
  Constraints.MinWidth = 185
  OnClose = FormClose
  OnCloseQuery = FormCloseQuery
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnKeyDown = FormKeyDown
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object LeftBevel: TUiBevel
    Left = 0
    Top = 37
    Width = 8
    Height = 237
    Align = alLeft
    Shape = bsSpacer
  end
  object RightBevel: TUiBevel
    Left = 354
    Top = 37
    Width = 8
    Height = 237
    Align = alRight
    Shape = bsSpacer
  end
  object DirPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 362
    Height = 37
    Align = alTop
    BevelOuter = bvNone
    TabOrder = 0
    DesignSize = (362, 37)
    object DirUpOneLevelBtn: TUiSpeedButton
      Left = 331
      Top = 8
      Hint = 'Up One Level'
      Anchors = [akTop, akRight]
      Flat = False
      ImageIndex = imgUpOneLevel
      Images = BcImages.MainImages
      OnClick = DirUpOneLevelClick
    end
    object DirEdit: TUiSpecBar
      Left = 8
      Top = 8
      Width = 315
      AcceptImageIndex = imgAccept
      Anchors = [akLeft, akTop, akRight]
      AutoCompleteEx = acDirs
      Images = BcImages.MainImages
      TabOrder = 0
      OnAcceptClick = DirAcceptClick
      OnBrowse = DirEditBrowse
      OnChange = DirEditChange
      OnUpdateTitles = DirEditUpdateTitles
    end
  end
  object ListView: TUiListView
    Left = 8
    Top = 37
    Width = 346
    Height = 237
    Align = alClient
    Columns = <
      item
        AutoSize = True
      end
    >
    ReadOnly = True
    RowSelect = True
    ShowColumnHeaders = False
    TabOrder = 1
    ViewStyle = vsReport
    OnDblClick = ListViewDblClick
    OnSelectItem = ListViewSelectItem
  end
  object NamePanel: TUiPanel
    Left = 0
    Top = 274
    Width = 362
    Height = 58
    Align = alBottom
    BevelOuter = bvNone
    TabOrder = 2
    DesignSize = (362, 58)
    object NameLbl: TUiLabel
      Left = 8
      Top = 12
      Height = 13
      Caption = 'File &name:'
      FocusControl = NameEdit
    end
    object FilterLbl: TUiLabel
      Left = 8
      Top = 41
      Height = 13
      Caption = 'Files of &type:'
      FocusControl = FilterEdit
    end
    object NameEdit: TUiComboBox
      Left = 79
      Top = 8
      Width = 274
      Height = 21
      Anchors = [akLeft, akTop, akRight]
      TabOrder = 0
      OnChange = NameEditChange
      IsMRU = True
    end
    object FilterEdit: TUiComboBox
      Left = 79
      Top = 37
      Width = 274
      Height = 21
      Style = csDropDownList
      Anchors = [akLeft, akTop, akRight]
      TabOrder = 1
      OnChange = FilterEditChange
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 332
    Width = 362
    TabOrder = 3
    SizeGripper = True
    object OkBtn: TUiOkBtn
      OnClick = OkClick
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
