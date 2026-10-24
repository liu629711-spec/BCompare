object ReportPreviewDialog: TReportPreviewDialog
  BorderIcons = [biSystemMenu, biMaximize]
  BorderStyle = bsSizeable
  Caption = 'Print Preview'
  ClientHeight = 409
  ClientWidth = 465
  Constraints.MinHeight = 98
  Constraints.MinWidth = 185
  OnCreate = FormCreate
  OnKeyDown = FormKeyDown
  OnResize = FormResize
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object ScrollBox: TUiScrollBox
    Left = 0
    Top = 0
    Width = 465
    Height = 409
    HorzScrollBar.Tracking = True
    VertScrollBar.Tracking = True
    Align = alClient
    Color = 15195073
    ParentColor = False
    TabOrder = 0
    OnMouseMove = PageMouseMove
    OnMouseUp = PageMouseUp
    OnMouseWheel = ScrollBoxMouseWheel
    object RightShadowShape: TShape
      Left = 385
      Top = 28
      Width = 3
      Height = 359
      Brush.Color = clGray
      Pen.Color = clGray
    end
    object BottomShadowShape: TShape
      Left = 84
      Top = 384
      Width = 301
      Height = 3
      Brush.Color = clGray
      Pen.Color = clGray
    end
    object Panel: TUiPanel
      Left = 80
      Top = 24
      Width = 305
      Height = 361
      BevelOuter = bvNone
      Color = clWhite
      FullRepaint = True
      ParentBackground = False
      TabOrder = 0
      OnMouseDown = PageMouseDown
      OnMouseMove = PageMouseMove
      OnMouseUp = PageMouseUp
      OnPaint = PanelPaint
      object Image: TUiImage
        Left = 0
        Top = 0
        Width = 305
        Height = 361
        Stretch = True
        OnMouseDown = PageMouseDown
        OnMouseMove = PageMouseMove
        OnMouseUp = PageMouseUp
      end
    end
  end
end
