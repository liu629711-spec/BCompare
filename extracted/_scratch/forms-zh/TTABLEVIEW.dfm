object TableView: TTableView
  HelpType = htKeyword
  HelpKeyword = 'ViewTable'
  object Thumbnail: TUiThumbnail
    Left = 0
    Top = 0
    Width = 39
    Height = 642
    Align = alLeft
    PopupMenu = ThumbnailPopup
    TabOrder = 0
    OnGetColors = ThumbnailGetColors
    OnGetPriority = ThumbnailGetPriority
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
    object InputPanel: TUiPanel
      Left = 0
      Top = 0
      Width = 711
      Height = 555
      Align = alClient
      BevelOuter = bvNone
      TabOrder = 0
      OnResize = InputPanelResize
      object Splitter: TUiSplitter
        Left = 354
        Top = 0
        Height = 555
        OnMoved = SplitterMoved
      end
      object LeftPanel: TUiPanel
        Left = 0
        Top = 0
        Width = 354
        Height = 555
        Align = alLeft
        BevelOuter = bvNone
        TabOrder = 0
      end
      object RightPanel: TUiPanel
        Left = 357
        Top = 0
        Width = 354
        Height = 555
        Align = alClient
        BevelOuter = bvNone
        TabOrder = 1
      end
    end
    object DetailsPanel: TUiPanel
      Left = 0
      Top = 555
      Width = 711
      Height = 68
      Align = alBottom
      BevelOuter = bvLowered
      TabOrder = 1
      OnResize = DetailsPanelResize
    end
    object Footer: TUiTabFooter
      Left = 0
      Top = 623
      Width = 711
      Height = 19
      Images = BcImages.HeaderImages
      PopupMenu = FooterPopup
      OnChange = FooterChange
      OnScroll = FooterScroll
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
        Width = 225
      end
    >
  end
  object ThumbnailPopup: TUiPopupMenu
    Left = 65
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
  object FooterPopup: TUiPopupMenu
    OnPopup = FooterListClick
    Left = 97
  end
end
