object BetaExpiredDialog: TBetaExpiredDialog
  Caption = 'Beta Expired'
  ClientHeight = 379
  OnCreate = FormCreate
  PixelsPerInch = 96
  TextHeight = 13
  object WebBrowser: TUiWebBrowser
    Top = 113
    TabOrder = 1
  end
  object ToDesktopPanel: TUiPanel
    Top = 327
    TabOrder = 2
  end
  object StatusBar: TUiStatusBar
    Top = 360
  end
  object ExpiredPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 411
    Height = 113
    Align = alTop
    TabOrder = 0
    object Image: TUiDlgIcon
      Left = 16
      Top = 16
      IconType = diApplication
    end
    object ProductNameLbl: TUiLabel
      Left = 64
      Top = 16
      Height = 22
      Caption = '%'
      Font.Charset = DEFAULT_CHARSET
      Font.Color = clWindowText
      Font.Height = -19
      Font.Name = 'Arial'
      Font.Style = []
      ParentFont = False
    end
    object Version: TUiLabel
      Left = 64
      Top = 42
      Height = 13
      Caption = '%'
    end
    object ThanksLbl: TUiLabel
      Left = 16
      Top = 63
      Height = 16
      Caption = 'Thanks for testing our beta!'
      Font.Charset = DEFAULT_CHARSET
      Font.Color = clWindowText
      Font.Height = -13
      Font.Name = 'Tahoma'
      Font.Style = []
      ParentFont = False
    end
    object HomePageLbl: TUiLabel
      Left = 16
      Top = 83
      Height = 13
      Caption = 'This beta has expired.  Please download a newer release.'
    end
  end
end
