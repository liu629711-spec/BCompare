object ReportSetupDialog: TReportSetupDialog
  Caption = 'Page Setup'
  ClientHeight = 283
  ClientWidth = 457
  OnClose = FormClose
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object MarginLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '%'
  end
  object MarginLeftLbl: TUiLabel
    Left = 8
    Top = 25
    Height = 13
    Caption = '&Left:'
    FocusControl = MarginLeftEdit
  end
  object MarginRightLbl: TUiLabel
    Left = 128
    Top = 25
    Height = 13
    Caption = '&Right:'
    FocusControl = MarginRightEdit
  end
  object MarginTopLbl: TUiLabel
    Left = 8
    Top = 71
    Height = 13
    Caption = '&Top:'
    FocusControl = MarginTopEdit
  end
  object MarginBottomLbl: TUiLabel
    Left = 128
    Top = 71
    Height = 13
    Caption = 'B&ottom:'
    FocusControl = MarginBottomEdit
  end
  object PreviewLbl: TUiLabel
    Left = 256
    Top = 8
    Height = 13
    Caption = 'Preview:'
  end
  object PreviewBevel: TUiBevel
    Left = 247
    Top = 8
    Width = 1
    Height = 236
    Shape = bsLeftLine
  end
  object MarginLeftEdit: TUiEdit
    Left = 8
    Top = 42
    Width = 49
    Height = 21
    TabOrder = 0
    OnChange = MarginEditChange
  end
  object MarginRightEdit: TUiEdit
    Left = 128
    Top = 42
    Width = 49
    Height = 21
    TabOrder = 1
    OnChange = MarginEditChange
  end
  object MarginTopEdit: TUiEdit
    Left = 8
    Top = 88
    Width = 49
    Height = 21
    TabOrder = 2
    OnChange = MarginEditChange
  end
  object MarginBottomEdit: TUiEdit
    Left = 128
    Top = 88
    Width = 49
    Height = 21
    TabOrder = 3
    OnChange = MarginEditChange
  end
  object MarginMaxBtn: TUiButton
    Left = 8
    Top = 117
    Caption = '&Max'
    TabOrder = 4
    OnClick = MarginMaxClick
    AutoSize = asLeft
  end
  object HeaderFontBtn: TUiButton
    Left = 8
    Top = 156
    Caption = '&Header Font...'
    TabOrder = 5
    OnClick = HeaderFontClick
    AutoSize = asLeft
  end
  object BodyFontBtn: TUiButton
    Left = 8
    Top = 187
    Caption = 'Bo&dy Font...'
    TabOrder = 6
    OnClick = BodyFontClick
    AutoSize = asLeft
  end
  object PageBreaksEdit: TUiCheckBox
    Left = 8
    Top = 218
    Height = 17
    Caption = 'Pa&ge breaks between reports'
    TabOrder = 7
  end
  object PreviewPanel: TUiPanel
    Left = 256
    Top = 21
    Width = 193
    Height = 223
    BevelOuter = bvNone
    TabOrder = 8
    object ShadowShape: TShape
      Left = 58
      Top = 44
      Width = 85
      Height = 110
      Brush.Color = clGray
      Pen.Style = psClear
    end
    object PageShape: TShape
      Left = 54
      Top = 40
      Width = 85
      Height = 110
    end
    object MarginShape: TShape
      Left = 62
      Top = 48
      Width = 69
      Height = 95
      Brush.Style = bsClear
      Pen.Style = psDot
    end
    object SampleLbl: TUiLabel
      Left = 84
      Top = 76
      Height = 36
      Caption = 'A'
      Font.Charset = DEFAULT_CHARSET
      Font.Color = clWindowText
      Font.Height = -32
      Font.Name = 'Times New Roman'
      Font.Style = [fsBold]
      ParentFont = False
      Transparent = True
    end
    object PortraitEdit: TUiRadioButton
      Left = 0
      Top = 185
      Height = 17
      Caption = '&Portrait'
      TabOrder = 0
      OnClick = OrientationClick
    end
    object LandscapeEdit: TUiRadioButton
      Left = 0
      Top = 206
      Height = 17
      Caption = 'L&andscape'
      TabOrder = 1
      OnClick = OrientationClick
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 244
    Width = 457
    TabOrder = 9
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
    object SetupBtn: TUiAdvancedBtn
      Caption = 'Print &Setup...'
      OnClick = SetupClick
    end
  end
end
