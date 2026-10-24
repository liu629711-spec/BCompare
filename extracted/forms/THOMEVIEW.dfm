object HomeView: THomeView
  HelpType = htKeyword
  HelpKeyword = 'ViewHome'
  ParentColor = False
  Caption = 'Home'
  object MainPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 750
    Height = 580
    Align = alClient
    BevelOuter = bvNone
    Color = 16382457
    ParentBackground = False
    TabOrder = 0
    OnResize = MainPanelResize
    object TopLineBevel: TUiBevel
      Left = 0
      Top = 0
      Width = 750
      Height = 2
      Align = alTop
      Shape = bsTopLine
    end
    object SessionsSplitter: TUiSplitter
      Left = 150
      Top = 2
      Width = 5
      Height = 578
      OnCanResize = SessionsSplitterCanResize
      OnMoved = SessionsSplitterMoved
    end
    object SessionsPanel: TUiPanel
      Left = 0
      Top = 2
      Width = 150
      Height = 578
      Align = alLeft
      BevelOuter = bvNone
      FullRepaint = True
      ParentBackground = False
      TabOrder = 0
      OnResize = SessionsPanelResize
      OnPaint = SessionsPanelPaint
      object SessionsLbl: TUiLabel
        Left = 8
        Top = 2
        Height = 14
        Caption = 'Sessions'
        FocusControl = SessionsTreeView
        FontSize = 1
      end
      object SessionsTreeView: TUiTreeView
        Left = 0
        Top = 24
        Width = 149
        Height = 523
        BorderStyle = bsNone
        Color = 15591395
        DragMode = dmAutomatic
        Images = BcImages.MainImages
        MultiSelect = True
        MultiSelectStyle = [msControlSelect, msShiftSelect, msVisibleOnly]
        PopupMenu = SessionsPopup
        TabOrder = 0
        OnCancelEdit = SessionsTreeViewCancelEdit
        OnChange = SessionsTreeViewChange
        OnCollapsed = SessionsTreeViewCollapsed
        OnDblClick = SessionsTreeViewDblClick
        OnDragDrop = SessionsTreeViewDragDrop
        OnDragOver = SessionsTreeViewDragOver
        OnEdited = SessionsTreeViewEdited
        OnEditing = SessionsTreeViewEditing
        OnExpanded = SessionsTreeViewExpanded
        OnKeyDown = SessionsTreeViewKeyDown
        OnKeyPress = SessionsTreeViewKeyPress
        AllowUnselected = True
      end
      object SessionsNewBtn: TUiBitBtn
        Left = 4
        Top = 551
        Width = 24
        Hint = 'New'
        ImageIndex = imgListAdd
        Images = BcImages.MainImages
        PopupMenu = SessionsNewPopup
        TabOrder = 1
        DropDownOnClick = True
      end
      object SessionsDeleteBtn: TUiBitBtn
        Left = 28
        Top = 551
        Width = 24
        Hint = 'Delete'
        ImageIndex = imgListDelete
        Images = BcImages.MainImages
        TabOrder = 2
        OnClick = SessionsDeleteClick
      end
      object SessionsSearchEdit: TUiSearchEdit
        Left = 56
        Top = 552
        Width = 90
        Height = 21
        TabOrder = 3
        OnChange = SessionsSearchEditChange
      end
    end
    object RightPanel: TUiPanel
      Left = 155
      Top = 2
      Width = 595
      Height = 578
      Align = alClient
      BevelOuter = bvNone
      FullRepaint = True
      ParentColor = True
      TabOrder = 1
      OnResize = RightPanelResize
      object WebShowImage: TUiImage
        Left = 579
        Top = 562
        Width = 16
        Height = 16
        Hint = 'Show Web Resources Panel'
        OnClick = WebShowClick
        ImageIndex = imgTriangleUp
        Images = BcImages.MainImages
      end
      object SpecPanel: TUiPanel
        Left = 0
        Top = 0
        Width = 595
        Height = 119
        BevelOuter = bvNone
        ParentColor = True
        TabOrder = 0
        OnResize = SpecPanelResize
        object SpecImage: TUiImage
          Left = 4
          Top = 4
          Width = 16
          Height = 16
          Images = BcImages.MainImages
        end
        object SpecLbl: TUiLabel
          Left = 24
          Top = 4
          Height = 16
          Caption = '%'
          FontSize = 2
        end
        object SpecLeftFrame: TFormattedSpecFrame
          Left = 4
          Top = 24
          Width = 587
          Height = 16
          TabOrder = 0
        end
        object SpecRightFrame: TFormattedSpecFrame
          Left = 4
          Top = 44
          Width = 587
          Height = 16
          TabOrder = 1
        end
        object SpecCenterFrame: TFormattedSpecFrame
          Left = 4
          Top = 64
          Width = 587
          Height = 16
          TabOrder = 2
        end
        object SpecEditDefaultBtn: TUiButton
          Left = 4
          Top = 88
          Caption = 'Edit Defaults'
          TabOrder = 3
          OnClick = SessionsEditClick
          AutoSize = asLeft
        end
        object SpecOpenBtn: TUiButton
          Left = 4
          Top = 88
          Caption = 'Open'
          TabOrder = 4
          OnClick = ManageOpenClick
          AutoSize = asLeft
        end
        object SpecEditBtn: TUiButton
          Left = 84
          Top = 88
          Caption = 'Edit'
          TabOrder = 5
          OnClick = SessionsEditClick
          AutoSize = asLeft
        end
      end
      object TaskPanel: TUiPanel
        Left = 0
        Top = 282
        Width = 595
        Height = 80
        BevelOuter = bvNone
        FullRepaint = True
        ParentColor = True
        TabOrder = 2
        OnDragDrop = TaskDragDrop
        OnDragOver = TaskDragOver
        object TaskTipLbl: TUiLabel
          Left = 231
          Top = 8
          Height = 14
          Caption = 'Drag folders or files onto session icon'
          FontSize = 1
        end
        object TaskTipDescLbl: TUiLabel
          Left = 224
          Top = 26
          Height = 13
          Caption = 'or click a session icon to begin:'
        end
      end
      object ManagePanel: TUiPanel
        Left = 0
        Top = 119
        Width = 432
        Height = 163
        BevelOuter = bvNone
        BorderWidth = 1
        Caption = 'Select a session to manage its settings'
        ParentBackground = False
        TabOrder = 1
        OnResize = ManagePanelResize
        OnPaint = ManagePanelPaint
        object ManageImage: TUiImage
          Left = 4
          Top = 4
          Width = 16
          Height = 16
          Images = BcImages.MainImages
        end
        object ManageLbl: TUiLabel
          Left = 24
          Top = 4
          Height = 16
          Caption = '%'
          FontSize = 2
        end
        object ManagePinImage: TUiImage
          Left = 376
          Top = 4
          Width = 16
          Height = 16
          OnClick = ManagePinClick
          ImageIndex = imgPin
          Images = BcImages.MainImages
        end
        object ManageMaximizeImage: TUiImage
          Left = 396
          Top = 4
          Width = 16
          Height = 16
          OnClick = ManageMaximizeClick
          Images = BcImages.MainImages
        end
        object ManageHideImage: TUiImage
          Left = 416
          Top = 4
          Width = 16
          Height = 16
          Hint = 'Hide Session Management Panel'
          OnClick = ManageHideClick
          ImageIndex = imgXGray
          Images = BcImages.MainImages
        end
        object ManagePageControl: TUiPageControl
          Left = 4
          Top = 24
          Width = 420
          Height = 100
          TabOrder = 0
        end
        object ManageOpenBtn: TUiButton
          Left = 4
          Top = 132
          Caption = 'Open'
          TabOrder = 1
          OnClick = ManageOpenClick
          AutoSize = asLeft
        end
        object ManageDefaultBtn: TUiButton
          Left = 84
          Top = 132
          Caption = 'Factory &Defaults'
          TabOrder = 2
          OnClick = ManageDefaultClick
          AutoSize = asLeft
        end
        object ManageLockBtn: TUiButton
          Left = 84
          Top = 132
          Caption = '%'
          TabOrder = 3
          OnClick = ManageLockClick
          AutoSize = asLeft
        end
        object ManageSaveBtn: TUiButton
          Left = 191
          Top = 132
          Caption = '&Save'
          TabOrder = 4
          OnClick = ManageSaveClick
          AutoSize = asRight
        end
        object ManageSaveAsBtn: TUiButton
          Left = 271
          Top = 132
          Caption = 'Save &As...'
          TabOrder = 5
          OnClick = ManageSaveAsClick
          AutoSize = asRight
        end
        object ManageCancelBtn: TUiButton
          Left = 351
          Top = 132
          Caption = 'Cancel'
          TabOrder = 6
          OnClick = ManageCancelClick
          AutoSize = asRight
        end
      end
    end
  end
  object WebShowPanel: TUiPanel
    Left = 0
    Top = 580
    Width = 750
    Height = 4
    Align = alBottom
    ParentBackground = False
    TabOrder = 1
  end
  object WebPanel: TUiPanel
    Left = 0
    Top = 584
    Width = 750
    Height = 100
    Align = alBottom
    BevelOuter = bvNone
    Color = 592285
    ParentBackground = False
    TabOrder = 2
    StyleElements = [seFont, seBorder]
    OnResize = WebPanelResize
    OnPaint = WebPanelPaint
    DesignSize = (750, 100)
    object KnowledgeBaseLbl: TUiLabel
      Left = 16
      Top = 16
      Height = 17
      Caption = 'KNOWLEDGE BASE'
      FontColor = 11328489
      FontSize = 1
      StyleElements = [seClient, seBorder]
      UseTitleFont = True
    end
    object KnowledgeBaseSearchImage: TUiImage
      Left = 168
      Top = 40
      Width = 16
      Height = 16
      OnClick = KnowledgeBaseSearchClick
      ImageIndex = imgKnowledgeBaseSearch
      Images = BcImages.MainImages
    end
    object KnowledgeBaseBox: TPaintBox
      Left = 201
      Top = 0
      Width = 2
      Height = 108
      OnPaint = WebBevelPaint
    end
    object ForumsLbl: TUiLabel
      Left = 217
      Top = 16
      Height = 17
      Caption = 'SUPPORT FORUMS'
      FontColor = 11328489
      FontSize = 1
      StyleElements = [seClient, seBorder]
      UseTitleFont = True
    end
    object ForumsLinkLbl: TUiLinkLabel
      Left = 217
      Top = 34
      Width = 161
      Height = 26
      Caption = 'Visit our <a href="%s">online forums</a> for technical support.'
      FontColor = clCream
      LinkFontColor = clWhite
      LinkFontStyle = [fsBold, fsUnderline]
      WordWrap = True
    end
    object ForumsBox: TPaintBox
      Left = 394
      Top = 0
      Width = 2
      Height = 108
      OnPaint = WebBevelPaint
    end
    object BetaWarnLbl: TUiLabel
      Left = 410
      Top = 16
      Height = 17
      Caption = '%'
      FontColor = 11328489
      FontSize = 1
      StyleElements = [seClient, seBorder]
      UseTitleFont = True
    end
    object BetaWarnLinkLbl: TUiLinkLabel
      Left = 410
      Top = 34
      Width = 161
      Height = 13
      Caption = '%'
      FontColor = clCream
      LinkFontColor = clWhite
      LinkFontStyle = [fsBold, fsUnderline]
      WordWrap = True
    end
    object BetaWarnShape: TShape
      Left = 400
      Top = 8
      Width = 182
      Height = 81
      Brush.Style = bsClear
      Pen.Color = clWhite
      Pen.Width = 4
      Shape = stRoundRect
    end
    object VideosLbl: TUiLabel
      Left = 410
      Top = 16
      Height = 17
      Caption = 'SCREENCASTS'
      FontColor = 11328489
      FontSize = 1
      StyleElements = [seClient, seBorder]
      UseTitleFont = True
    end
    object VideosLinkLbl: TUiLinkLabel
      Left = 410
      Top = 34
      Width = 161
      Height = 39
      Caption = 'Watch our <a href="%s">online videos</a> for tips on getting the most out of Beyond Compare.'
      FontColor = clCream
      LinkFontColor = clWhite
      LinkFontStyle = [fsBold, fsUnderline]
      WordWrap = True
    end
    object VideosBox: TPaintBox
      Left = 587
      Top = 0
      Width = 2
      Height = 108
      OnPaint = WebBevelPaint
    end
    object LicenseExpiringShape: TShape
      Left = 594
      Top = 8
      Width = 182
      Height = 81
      Brush.Style = bsClear
      Pen.Color = clWhite
      Pen.Width = 4
      Shape = stRoundRect
    end
    object RegisterLbl: TUiLabel
      Left = 603
      Top = 16
      Height = 17
      Caption = 'REGISTER'
      FontColor = 11328489
      FontSize = 1
      StyleElements = [seClient, seBorder]
      UseTitleFont = True
    end
    object RegisterLinkLbl: TUiLinkLabel
      Left = 603
      Top = 34
      Width = 161
      Height = 39
      Caption = 'Running in trial mode.  <a href="register">Enter your version %0:d license key</a> or visit <a href="%1:s">our online shop</a>.'
      FontColor = clCream
      LinkFontColor = clWhite
      LinkFontStyle = [fsBold, fsUnderline]
      WordWrap = True
      OnURLClick = RegisterLinkLblURLClick
    end
    object RegisterBox: TPaintBox
      Left = 780
      Top = 0
      Width = 2
      Height = 108
      OnPaint = WebBevelPaint
    end
    object MsgLbl: TUiLabel
      Left = 796
      Top = 16
      Height = 17
      Caption = '%'
      FontColor = 11328489
      FontSize = 1
      StyleElements = [seClient, seBorder]
      UseTitleFont = True
    end
    object MsgLinkLbl: TUiLinkLabel
      Left = 796
      Top = 34
      Width = 161
      Height = 13
      Caption = '%'
      FontColor = clCream
      LinkFontColor = clWhite
      LinkFontStyle = [fsBold, fsUnderline]
      WordWrap = True
    end
    object MsgBox: TPaintBox
      Left = 973
      Top = 0
      Width = 2
      Height = 108
      OnPaint = WebBevelPaint
    end
    object WebHideImage: TUiImage
      Left = 732
      Top = 4
      Width = 16
      Height = 16
      Hint = 'Hide Web Resources Panel'
      Anchors = [akTop, akRight]
      OnClick = WebHideClick
      ImageIndex = imgXWhite
      Images = BcImages.MainImages
    end
    object StickerImage: TUiImage
      Left = 630
      Top = 6
      Width = 98
      Height = 98
      Cursor = crHandPoint
      Anchors = [akTop, akRight]
      Picture.Data = {TPngImage 15631 bytes}
      OnClick = StickerClick
    end
    object KnowledgeBaseEdit: TUiEdit
      Left = 16
      Top = 38
      Width = 144
      Height = 21
      TabOrder = 0
    end
  end
  object MessagePanel: TUiPanel
    TabOrder = 3
  end
  object StatusBar: TUiStatusBar
    Visible = False
  end
  object SessionsPopup: TUiPopupMenu
    object SessionsOpenItem: TUiMenuItem
      Caption = 'Open'
      OnClick = ManageOpenClick
    end
    object SessionsOpenAsListItem: TUiSubmenuItem
      Caption = 'Open as New'
    end
    object SessionsFolderOpenItem: TUiMenuItem
      Caption = 'Open Sessions'
      OnClick = SessionsFolderOpenClick
    end
    object SessionsSeparator1Item: TUiSeparatorItem
    end
    object SessionsNewListItem: TUiSubmenuItem
      Caption = 'New'
      OnClick = SessionsNewListClick
    end
    object SessionsClearItem: TUiMenuItem
      Caption = 'Clear Contents'
      OnClick = SessionsClearClick
    end
    object SessionsDeleteItem: TUiMenuItem
      Caption = 'Delete'
      ShortCut = 46
      OnClick = SessionsDeleteClick
    end
    object SessionsSaveAsItem: TUiMenuItem
      Caption = 'Save As...'
      OnClick = ManageSaveAsClick
    end
    object SessionsLockItem: TUiMenuItem
      Caption = '%'
      OnClick = ManageLockClick
    end
    object SessionsRenameItem: TUiMenuItem
      Caption = 'Rename'
      ShortCut = 113
      OnClick = SessionsRenameClick
    end
    object SessionsEditItem: TUiMenuItem
      Caption = 'Edit'
      OnClick = SessionsEditClick
    end
    object SessionsSeparator2Item: TUiSeparatorItem
    end
    object SessionsExpandAllItem: TUiMenuItem
      Caption = 'Expand All'
      OnClick = SessionsExpandAllClick
    end
    object SessionsCollapseAllItem: TUiMenuItem
      Caption = 'Collapse All'
      OnClick = SessionsCollapseAllClick
    end
  end
  object SessionsNewPopup: TUiPopupMenu
    Images = BcImages.MainImages
    OnPopup = SessionsNewListClick
    Left = 32
  end
  object TaskPopup: TUiPopupMenu
    OnPopup = TaskPopupPopup
    Left = 64
    object TaskIsFavItem: TUiMenuItem
      Caption = 'Favorite'
      OnClick = TaskIsFavClick
    end
  end
end
