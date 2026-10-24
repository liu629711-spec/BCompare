object HexView: THexView
  HelpType = htKeyword
  HelpKeyword = 'ViewHex'
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
    object Splitter: TUiSplitter
      Left = 354
      Top = 0
      Height = 642
      OnMoved = SplitterMoved
    end
    object LeftPanel: TUiPanel
      Left = 0
      Top = 0
      Width = 354
      Height = 642
      Align = alLeft
      BevelOuter = bvNone
      TabOrder = 0
    end
    object RightPanel: TUiPanel
      Left = 357
      Top = 0
      Width = 354
      Height = 642
      Align = alClient
      BevelOuter = bvNone
      TabOrder = 1
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
        Alignment = taCenter
        Width = 70
      end
      item
        Width = 225
      end
    >
  end
  object ThumbnailPopup: TUiPopupMenu
    Left = 64
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
