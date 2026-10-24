object TextView: TTextView
  HelpType = htKeyword
  HelpKeyword = 'ViewText'
  object InThumbnail: TUiThumbnail
    Left = 0
    Top = 0
    Width = 39
    Height = 642
    Align = alLeft
    PopupMenu = ThumbnailPopup
    TabOrder = 0
    OnGetColors = InThumbnailGetColors
    OnGetPriority = InThumbnailGetPriority
    OnLock = ThumbnailLock
    OnRequestMoveBy = ThumbnailRequestMoveBy
    OnRequestMoveTo = ThumbnailRequestMoveTo
    OnUnlock = ThumbnailUnlock
  end
  object MainPanel: TUiPanel
    Left = 39
    Top = 0
    Width = 711
    Height = 642
    Align = alClient
    BevelOuter = bvNone
    TabOrder = 1
    OnResize = MainPanelResize
    object OutputSplitter: TUiSplitter
      Left = 0
      Top = 320
      Width = 711
      Height = 3
      Cursor = crVSplit
      Align = alTop
      OnMoved = OutputSplitterMoved
    end
    object ComparePanel: TUiPanel
      Left = 0
      Top = 0
      Width = 711
      Height = 320
      Align = alTop
      BevelOuter = bvNone
      TabOrder = 0
      object InputPanel: TUiPanel
        Left = 0
        Top = 0
        Width = 711
        Height = 248
        Align = alClient
        BevelOuter = bvNone
        TabOrder = 0
        OnResize = InputPanelResize
        object Splitter: TUiSplitter
          Left = 235
          Top = 0
          Height = 248
          OnMoved = SplitterMoved
        end
        object CenterSplitter: TUiSplitter
          Left = 473
          Top = 0
          Height = 248
          Align = alRight
          OnMoved = CenterSplitterMoved
        end
        object LeftPanel: TUiPanel
          Left = 0
          Top = 0
          Width = 235
          Height = 248
          Align = alLeft
          BevelOuter = bvNone
          TabOrder = 0
          OnResize = EditorPanelResize
        end
        object CenterPanel: TUiPanel
          Left = 238
          Top = 0
          Width = 235
          Height = 248
          Align = alClient
          BevelOuter = bvNone
          TabOrder = 1
          OnResize = EditorPanelResize
        end
        object RightPanel: TUiPanel
          Left = 476
          Top = 0
          Width = 235
          Height = 248
          Align = alRight
          BevelOuter = bvNone
          TabOrder = 2
          OnResize = EditorPanelResize
        end
      end
      object DetailsPanel: TUiPanel
        Left = 0
        Top = 248
        Width = 711
        Height = 72
        Align = alBottom
        BevelOuter = bvLowered
        Color = clBtnShadow
        ParentBackground = False
        TabOrder = 1
        OnResize = DetailsPanelResize
      end
    end
    object OutputPanel: TUiPanel
      Left = 0
      Top = 323
      Width = 711
      Height = 319
      Align = alClient
      BevelOuter = bvNone
      TabOrder = 1
      object OutThumbnail: TUiThumbnail
        Left = 0
        Top = 0
        Width = 39
        Height = 319
        Align = alLeft
        PopupMenu = ThumbnailPopup
        TabOrder = 0
        OnGetColors = OutThumbnailGetColors
        OnGetPriority = OutThumbnailGetPriority
        OnLock = ThumbnailLock
        OnRequestMoveBy = ThumbnailRequestMoveBy
        OnRequestMoveTo = ThumbnailRequestMoveTo
        OnUnlock = ThumbnailUnlock
      end
    end
  end
  object JobProgressPanel: TUiPanel
    TabOrder = 2
  end
  object JobErrorPanel: TUiPanel
    TabOrder = 3
  end
  object MessagePanel: TUiPanel
    TabOrder = 4
  end
  object StatusBar: TUiStatusBar
    Panels = <
      item
        Style = psOwnerDraw
        Width = 225
        Images = BcImages.ContentImages
      end
      item
        Width = 300
      end
      item
        Alignment = taCenter
        Width = 70
      end
      item
        Width = 225
      end
    >
  end
  object GapPopup: TUiPopupMenu
    OnPopup = GapListClick
    Left = 64
    object GapCollapseItem: TUiMenuItem
      Caption = 'Collapse Filtered Gap'
      Hint = 'Hides range of lines not matching display filter.'
      OnClick = GapExpandedClick
    end
    object GapExpandItem: TUiMenuItem
      Caption = 'Expand Filtered Gap'
      Hint = 'Shows range of lines not matching display filter.'
      OnClick = GapExpandedClick
    end
    object GapShowBarsItem: TUiMenuItem
      AutoCheck = True
      Caption = 'Show Filtered Line Counts'
      Hint = 'Shows or hides filtered line counts.'
      OnClick = GapShowBarsClick
    end
  end
  object NavPopup: TUiPopupMenu
    OnPopup = NavListClick
    Left = 96
  end
  object ThumbnailPopup: TUiPopupMenu
    Left = 128
    object ThumbnailScrollItem: TUiMenuItem
      AutoCheck = True
      Caption = 'Allow Scrolling'
      Hint = 'Allows scrolling of thumbnail view of large files, instead of compressing the thumbnail to fit.'
      OnClick = ThumbnailScrollClick
    end
    object ThumbnailHideItem: TUiMenuItem
      Caption = 'Hide Thumbnail'
      Hint = 'Hides thumbnail view.'
      OnClick = ThumbnailHideClick
    end
  end
end
