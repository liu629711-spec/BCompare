object RegView: TRegView
  HelpType = htKeyword
  HelpKeyword = 'ViewReg'
  OnResize = ViewResize
  object MainPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 750
    Height = 586
    Align = alClient
    BevelOuter = bvNone
    TabOrder = 0
    OnResize = MainPanelResize
    object Splitter: TUiSplitter
      Left = 373
      Top = 0
      Height = 586
      OnMoved = SplitterMoved
    end
    object LeftPanel: TUiPanel
      Left = 0
      Top = 0
      Width = 373
      Height = 586
      Align = alLeft
      BevelOuter = bvNone
      TabOrder = 0
    end
    object RightPanel: TUiPanel
      Left = 376
      Top = 0
      Width = 374
      Height = 586
      Align = alClient
      BevelOuter = bvNone
      TabOrder = 1
    end
  end
  object DetailsPanel: TUiPanel
    Left = 0
    Top = 586
    Width = 750
    Height = 56
    Align = alBottom
    BevelOuter = bvLowered
    Color = clBtnShadow
    ParentBackground = False
    TabOrder = 1
    OnResize = DetailsPanelResize
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
end
