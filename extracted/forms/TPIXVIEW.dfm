object PixView: TPixView
  HelpType = htKeyword
  HelpKeyword = 'ViewPix'
  OnResize = ViewResize
  object MainPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 750
    Height = 642
    Align = alClient
    BevelOuter = bvNone
    TabOrder = 0
    object TagSplitter: TUiSplitter
      Left = 700
      Top = 0
      Width = 5
      Height = 642
      Align = alRight
      OnCanResize = TagSplitterCanResize
      OnMoved = TagSplitterMoved
    end
    object NonTagPanel: TUiPanel
      Left = 0
      Top = 0
      Width = 700
      Height = 642
      Align = alClient
      BevelOuter = bvNone
      Color = 2305582
      ParentBackground = False
      TabOrder = 0
      OnResize = NonTagPanelResize
      object Splitter: TUiSplitter
        Left = 375
        Top = 0
        Width = 5
        Height = 316
        OnMoved = SplitterMoved
        OnPaint = SplitterPaint
      end
      object CenterSplitter: TUiSplitter
        Left = 0
        Top = 316
        Width = 700
        Height = 5
        Cursor = crVSplit
        Align = alBottom
        OnCanResize = CenterSplitterCanResize
        OnMoved = CenterSplitterMoved
        OnPaint = SplitterPaint
      end
      object LeftPanel: TUiPanel
        Left = 0
        Top = 0
        Width = 375
        Height = 316
        Align = alLeft
        BevelOuter = bvNone
        ParentBackground = False
        ParentColor = True
        TabOrder = 0
        object LeftImagePanel: TUiPanel
          Left = 0
          Top = 0
          Width = 375
          Height = 316
          Align = alClient
          BevelOuter = bvNone
          ParentColor = True
          TabOrder = 0
          OnMouseMove = ImageMouseMove
          OnMouseWheel = ImageMouseWheel
          OnMouseWheelHorz = ImageMouseWheelHorz
          OnPaint = ImagePanelPaint
          object LeftScrollBox: TUiScrollBox
            Left = 161
            Top = 134
            Width = 52
            Height = 52
            HorzScrollBar.Tracking = True
            VertScrollBar.Tracking = True
            BorderStyle = bsNone
            DoubleBuffered = True
            ParentDoubleBuffered = False
            TabOrder = 0
            OnMouseDown = ImageMouseDown
            OnMouseMove = ImageMouseMove
            OnMouseUp = ImageMouseUp
            OnMouseWheel = ImageMouseWheel
            OnKeyDown = ScrollBoxKeyDown
            OnMouseWheelHorz = ImageMouseWheelHorz
            OnScroll = ScrollBoxScroll
            object LeftImage: TUiImage
              Left = 0
              Top = 0
              Width = 48
              Height = 48
              OnMouseDown = ImageMouseDown
              OnMouseMove = ImageMouseMove
              OnMouseUp = ImageMouseUp
              OnPaint = ImagePaint
            end
          end
        end
      end
      object RightPanel: TUiPanel
        Left = 380
        Top = 0
        Width = 320
        Height = 316
        Align = alClient
        BevelOuter = bvNone
        ParentBackground = False
        ParentColor = True
        TabOrder = 1
        object RightImagePanel: TUiPanel
          Left = 0
          Top = 0
          Width = 320
          Height = 316
          Align = alClient
          BevelOuter = bvNone
          ParentColor = True
          TabOrder = 0
          OnMouseMove = ImageMouseMove
          OnMouseWheel = ImageMouseWheel
          OnMouseWheelHorz = ImageMouseWheelHorz
          OnPaint = ImagePanelPaint
          object RightScrollBox: TUiScrollBox
            Left = 161
            Top = 134
            Width = 52
            Height = 52
            HorzScrollBar.Tracking = True
            VertScrollBar.Tracking = True
            BorderStyle = bsNone
            DoubleBuffered = True
            ParentDoubleBuffered = False
            TabOrder = 0
            OnMouseDown = ImageMouseDown
            OnMouseMove = ImageMouseMove
            OnMouseUp = ImageMouseUp
            OnMouseWheel = ImageMouseWheel
            OnKeyDown = ScrollBoxKeyDown
            OnMouseWheelHorz = ImageMouseWheelHorz
            OnScroll = ScrollBoxScroll
            object RightImage: TUiImage
              Left = 0
              Top = 0
              Width = 48
              Height = 48
              OnMouseDown = ImageMouseDown
              OnMouseMove = ImageMouseMove
              OnMouseUp = ImageMouseUp
              OnPaint = ImagePaint
            end
          end
        end
      end
      object CenterPanel: TUiPanel
        Left = 0
        Top = 321
        Width = 700
        Height = 321
        Align = alBottom
        BevelOuter = bvNone
        ParentBackground = False
        ParentColor = True
        TabOrder = 2
        object ViewPanel: TUiPanel
          Left = 0
          Top = 0
          Width = 200
          Height = 321
          Align = alLeft
          BevelOuter = bvNone
          ParentColor = True
          TabOrder = 0
          OnMouseMove = ImageMouseMove
          object OffsetLbl: TUiLabel
            Left = 8
            Top = 8
            Height = 13
            Caption = 'Offset:'
            OnClick = OffsetResetClick
            FontColor = 16382457
          end
          object OffsetEditLbl: TUiLabel
            Left = 43
            Top = 8
            Height = 13
            Caption = '%'
            OnClick = OffsetResetClick
            FontColor = 16382457
          end
          object ZoomLbl: TUiLabel
            Left = 8
            Top = 29
            Height = 13
            Caption = 'Zoom:'
            FontColor = 16382457
          end
          object ZoomEditLbl: TUiLabel
            Left = 38
            Top = 29
            Height = 13
            Caption = '%'
            FontColor = 16382457
          end
          object ZoomActualBtn: TUiSpeedButton
            Left = 146
            Top = 46
            Flat = False
            ImageIndex = imgPixZoomActual
            Images = BcImages.MainImages
          end
          object ZoomFitBtn: TUiSpeedButton
            Left = 169
            Top = 46
            Flat = False
            ImageIndex = imgPixZoomFit
            Images = BcImages.MainImages
          end
          object DetailsLbl: TUiLabel
            Left = 8
            Top = 124
            Height = 13
            Caption = 'Pixel details:'
            FontColor = 16382457
          end
          object LeftDetailsInfoLbl: TUiLabel
            Left = 8
            Top = 234
            Height = 13
            Caption = '%'
            FontColor = 16382457
          end
          object RightDetailsInfoLbl: TUiLabel
            Left = 103
            Top = 234
            Height = 13
            Caption = '%'
            FontColor = 16382457
          end
          object ZoomEdit: TUiTrackBar
            Left = 0
            Top = 46
            Width = 146
            Height = 25
            Max = 2000
            Min = 1
            Position = 1
            ShowSelRange = False
            TabOrder = 0
            TickStyle = tsNone
            OnChange = ZoomEditChange
            OnMouseWheel = ZoomEditMouseWheel
          end
          object DiffModePanelView: TUiActivePanelView
            Left = 0
            Top = 66
            Width = 200
            Height = 58
            ParentColor = True
            TabOrder = 1
            object TolerancePanel: TUiActivePanel
              ParentColor = True
              object ToleranceLbl: TUiLabel
                Left = 8
                Top = 8
                Height = 13
                Caption = 'Tolerance:'
                FontColor = 16382457
              end
              object ToleranceEditLbl: TUiLabel
                Left = 59
                Top = 8
                Height = 13
                Caption = '%'
                FontColor = 16382457
              end
              object ToleranceGhostBtn: TUiSpeedButton
                Left = 169
                Top = 25
                Hint = 'Ghost Mode|Shows or hides ghost of pictures.'
                AutoCheck = True
                Flat = False
                ImageIndex = imgPixToleranceGhost
                Images = BcImages.MainImages
                OnClick = ToleranceGhostClick
              end
              object ToleranceEdit: TUiTrackBar
                Left = 0
                Top = 25
                Width = 169
                Height = 25
                Max = 255
                ShowSelRange = False
                TabOrder = 0
                TickStyle = tsNone
                OnChange = ToleranceEditChange
              end
            end
            object BlendPanel: TUiActivePanel
              ParentColor = True
              object BlendLbl: TUiLabel
                Left = 8
                Top = 8
                Height = 13
                Caption = 'Blend:'
                FontColor = 16382457
              end
              object BlendEditLbl: TUiLabel
                Left = 38
                Top = 8
                Height = 13
                Caption = '%'
                FontColor = 16382457
              end
              object BlendToggleBtn: TUiSpeedButton
                Left = 169
                Top = 25
                Flat = False
                ImageIndex = imgPixBlendToggle
                Images = BcImages.MainImages
              end
              object BlendEdit: TUiTrackBar
                Left = 0
                Top = 25
                Width = 169
                Height = 25
                Max = 100
                ShowSelRange = False
                TabOrder = 0
                TickStyle = tsNone
                OnChange = BlendEditChange
              end
            end
          end
          object LeftDetailsColorsPanel: TUiPanel
            Left = 8
            Top = 141
            Width = 89
            Height = 89
            BevelOuter = bvNone
            ParentBackground = False
            ParentColor = True
            TabOrder = 2
            OnPaint = DetailsColorsPanelPaint
          end
          object RightDetailsColorsPanel: TUiPanel
            Left = 103
            Top = 141
            Width = 89
            Height = 89
            BevelOuter = bvNone
            ParentBackground = False
            ParentColor = True
            TabOrder = 3
            OnPaint = DetailsColorsPanelPaint
          end
        end
        object CenterImagePanel: TUiPanel
          Left = 200
          Top = 0
          Width = 500
          Height = 321
          Align = alClient
          BevelOuter = bvNone
          ParentColor = True
          TabOrder = 1
          OnMouseMove = ImageMouseMove
          OnMouseWheel = ImageMouseWheel
          OnMouseWheelHorz = ImageMouseWheelHorz
          OnPaint = ImagePanelPaint
          object CenterScrollBox: TUiScrollBox
            Left = 149
            Top = 134
            Width = 52
            Height = 52
            HorzScrollBar.Tracking = True
            VertScrollBar.Tracking = True
            BorderStyle = bsNone
            DoubleBuffered = True
            ParentDoubleBuffered = False
            TabOrder = 0
            OnMouseDown = ImageMouseDown
            OnMouseMove = ImageMouseMove
            OnMouseUp = ImageMouseUp
            OnMouseWheel = ImageMouseWheel
            OnKeyDown = ScrollBoxKeyDown
            OnMouseWheelHorz = ImageMouseWheelHorz
            OnScroll = ScrollBoxScroll
            object CenterImage: TUiImage
              Left = 0
              Top = 0
              Width = 48
              Height = 48
              OnMouseDown = ImageMouseDown
              OnMouseMove = ImageMouseMove
              OnMouseUp = ImageMouseUp
            end
          end
        end
      end
    end
    object TagPanel: TUiPanel
      Left = 705
      Top = 0
      Width = 45
      Height = 642
      Align = alRight
      BevelOuter = bvNone
      ParentBackground = False
      ParentColor = True
      TabOrder = 1
    end
  end
  object JobProgressPanel: TUiPanel
    TabOrder = 1
  end
  object JobErrorPanel: TUiPanel
    TabOrder = 2
  end
  object MessagePanel: TUiPanel
    TabOrder = 3
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
  object DragTimer: TTimer
    Enabled = False
    Interval = 50
    OnTimer = DragTimerTimer
    Left = 64
  end
end
