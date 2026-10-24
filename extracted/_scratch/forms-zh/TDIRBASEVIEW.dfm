object DirBaseView: TDirBaseView
  OnResize = ViewResize
  object LogSplitter: TUiSplitter
    Left = 0
    Top = 628
    Width = 750
    Height = 3
    Cursor = crVSplit
    Align = alBottom
    AutoSnap = True
    OnCanResize = LogSplitterCanResize
    OnMoved = LogSplitterMoved
  end
  object MainPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 750
    Height = 581
    Align = alClient
    BevelOuter = bvNone
    TabOrder = 0
    object OtherFiltersPanel: TUiPanel
      Left = 0
      Top = 558
      Width = 750
      Height = 23
      Align = alBottom
      BevelOuter = bvNone
      TabOrder = 0
      OnResize = OtherFiltersPanelResize
      object OtherFiltersBevel: TUiBevel
        Left = 0
        Top = 0
        Width = 29
        Height = 23
        Align = alLeft
        Shape = bsSpacer
      end
      object OtherFiltersBtn: TUiSpeedButton
        Left = 0
        Top = 2
        Hint = 'Other Filters|Edits other file filters.'
        ImageIndex = imgFilters
        Images = BcImages.MainImages
        OnClick = OtherFiltersClick
      end
      object OtherFiltersLbl: TUiLabel
        Left = 30
        Top = 4
        Height = 13
        Caption = '%'
        ShowAccelChar = False
        Layout = tlCenter
        OnClick = OtherFiltersClick
      end
      object PeekInvisibleFilesImage: TUiImage
        Left = 540
        Top = 4
        Width = 16
        Height = 16
        ImageIndex = imgWarning
        Images = BcImages.MainImages
      end
      object PeekInvisibleFilesLbl: TUiLabel
        Left = 560
        Top = 4
        Height = 13
        Caption = 'Files in excluded folders are not visible'
      end
    end
  end
  object MessagePanel: TUiPanel
    Top = 581
    TabOrder = 1
  end
  object LogFrame: TLogFrame
    Left = 0
    Top = 631
    Width = 750
    Height = 100
    Align = alBottom
    PopupMenu = LogPopup
    TabOrder = 2
    object ListBox: TUiVirtualListBox
      Width = 729
      PopupMenu = LogPopup
    end
  end
  object StatusBar: TUiStatusBar
    OnResize = StatusBarResize
  end
  object ColPopup: TUiPopupMenu
    OnPopup = ColListClick
    Left = 32
  end
  object LogPopup: TUiPopupMenu
    Left = 64
    object LogClearItem: TUiMenuItem
      Caption = 'Clear Messages'
      Hint = 'Clears all messages from log.'
      OnClick = LogClearClick
    end
    object LogSaveItem: TUiMenuItem
      Caption = 'Save to File...'
      Hint = 'Saves log to file.'
      OnClick = LogSaveClick
    end
    object LogCopyToClipboardItem: TUiMenuItem
      Caption = 'Copy to Clipboard'
      Hint = 'Copies selected log messages to clipboard.'
      OnClick = LogCopyToClipboardClick
    end
    object LogSeparatorItem: TUiSeparatorItem
    end
    object LogHideItem: TUiMenuItem
      Caption = 'Hide Log'
      Hint = 'Hides log panel.'
      OnClick = LogHideClick
    end
  end
  object TreeViewSelTimer: TTimer
    Enabled = False
    Interval = 100
    OnTimer = TreeViewSelTimerTimer
    Left = 96
  end
  object StopTimer: TTimer
    Enabled = False
    Interval = 250
    OnTimer = StopTimerTimer
    Left = 128
  end
end
