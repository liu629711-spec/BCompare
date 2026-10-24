object CheckForUpdatesDialog: TCheckForUpdatesDialog
  BorderStyle = bsSizeable
  Caption = 'Program Updates and News'
  ClientHeight = 266
  ClientWidth = 411
  Constraints.MinHeight = 128
  Constraints.MinWidth = 185
  OnClose = FormClose
  OnKeyDown = FormKeyDown
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object WebBrowser: TUiWebBrowser
    Left = 0
    Top = 0
    Width = 411
    Height = 214
    Align = alClient
    TabOrder = 0
    OnStatusTextChange = WebBrowserStatusTextChange
    OnNavigateError = WebBrowserNavigateError
    OnCanNavigate = WebBrowserCanNavigate
  end
  object ToDesktopPanel: TUiPanel
    Left = 0
    Top = 214
    Width = 411
    Height = 33
    Align = alBottom
    BevelOuter = bvNone
    TabOrder = 1
    OnPaint = ToDesktopPanelPaint
    object ToDesktopEdit: TUiCheckBox
      Left = 8
      Top = 8
      Height = 17
      Caption = '&Download to Desktop only'
      TabOrder = 0
    end
  end
  object StatusBar: TUiStatusBar
    Left = 0
    Top = 247
    Width = 411
    Height = 19
    Panels = <
    >
    SimplePanel = True
  end
end
