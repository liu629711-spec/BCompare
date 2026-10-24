object DownloadUpdateDialog: TDownloadUpdateDialog
  BorderIcons = [biSystemMenu, biMinimize]
  BorderStyle = bsSingle
  Caption = '%'
  ClientHeight = 131
  ClientWidth = 431
  OnClose = FormClose
  OnCloseQuery = FormCloseQuery
  OnCreate = FormCreate
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object PanelView: TUiActivePanelView
    Left = 0
    Top = 0
    Width = 431
    Height = 71
    Align = alClient
    TabOrder = 0
    object DownloadingPanel: TUiActivePanel
      object DownloadingImage: TUiImage
        Left = 16
        Top = 16
        Width = 32
        Height = 32
        Picture.Data = {TPngImage 3863 bytes}
        Stretch = True
        Transparent = True
      end
      object DownloadingLbl: TUiLabel
        Left = 64
        Top = 16
        Height = 13
        Caption = 'Downloading...'
      end
      object ProgressLbl: TUiLabel
        Left = 412
        Top = 16
        Width = 11
        Height = 13
        Alignment = taRightJustify
        Caption = '%'
      end
      object RateLbl: TUiLabel
        Left = 64
        Top = 58
        Height = 13
        Caption = '%'
      end
      object RemainingLbl: TUiLabel
        Left = 412
        Top = 58
        Width = 11
        Height = 13
        Alignment = taRightJustify
        Caption = '%'
      end
      object DownloadingProgressBar: TUiProgressBar
        Left = 64
        Top = 33
        Width = 359
        Height = 17
        Max = 2800000
        TabOrder = 0
      end
    end
    object ConfirmPanel: TUiActivePanel
      object WarnImage: TUiDlgIcon
        Left = 16
        Top = 16
        IconType = diWarning
      end
      object WarnLbl: TUiLabel
        Left = 64
        Top = 16
        Width = 359
        Height = 26
        Caption = 'Clicking "Install" will close all Beyond Compare windows and run the downloaded file.  Save your work first!'
        WordWrap = True
      end
    end
    object ErrorPanel: TUiActivePanel
      object ErrorImage: TUiDlgIcon
        Left = 16
        Top = 16
        IconType = diError
      end
      object ErrorLbl: TUiLabel
        Left = 64
        Top = 16
        Height = 13
        Caption = 'Error downloading file.'
      end
    end
    object ToDesktopPanel: TUiActivePanel
      object ToDesktopImage: TUiDlgIcon
        Left = 16
        Top = 16
        IconType = diInformation
      end
      object ToDesktopLbl: TUiLabel
        Left = 64
        Top = 16
        Width = 359
        Height = 26
        Caption = 'Download complete.  To install, close all Beyond Compare windows and run the setup program on your desktop.'
        WordWrap = True
      end
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 71
    Width = 431
    Height = 60
    TabOrder = 1
    ItemTop = 29
    object LocationLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = '%'
      FontColor = cl3DDkShadow
    end
    object OkBtn: TUiOkBtn
      Caption = '&Install'
      OnClick = BtnClick
    end
    object CancelBtn: TUiCancelBtn
      OnClick = BtnClick
    end
    object CloseBtn: TUiCloseBtn
    end
  end
  object Timer: TTimer
    Enabled = False
    OnTimer = TimerTimer
  end
end
