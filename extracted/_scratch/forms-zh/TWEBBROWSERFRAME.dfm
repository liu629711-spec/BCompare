object WebBrowserFrame: TWebBrowserFrame
  Left = 0
  Top = 0
  Width = 569
  Height = 491
  TabOrder = 0
  object WebBrowser: TUiWebBrowser
    Left = 0
    Top = 0
    Width = 569
    Height = 467
    Align = alClient
    TabOrder = 0
    OnStatusTextChange = WebBrowserStatusTextChange
    OnHistoryChange = WebBrowserHistoryChange
    OnRefresh = WebBrowserRefresh
  end
  object BtnPanel: TUiPanel
    Left = 0
    Top = 467
    Width = 569
    Height = 24
    Align = alBottom
    TabOrder = 1
    object BackBtn: TUiSpeedButton
      Left = 0
      Top = 0
      Hint = 'Back'
      ImageIndex = imgWebBrowserBack
      Images = BcImages.MainImages
      OnClick = BackClick
    end
    object ForwardBtn: TUiSpeedButton
      Left = 23
      Top = 0
      Hint = 'Forward'
      ImageIndex = imgWebBrowserForward
      Images = BcImages.MainImages
      OnClick = ForwardClick
    end
    object RefreshBtn: TUiSpeedButton
      Left = 46
      Top = 0
      Hint = 'Refresh'
      ImageIndex = imgWebBrowserRefresh
      Images = BcImages.MainImages
      OnClick = RefreshClick
    end
    object StatusLbl: TUiLabel
      Left = 77
      Top = 4
      Height = 13
      Caption = '%'
    end
  end
end
