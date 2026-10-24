object AboutDialog: TAboutDialog
  Caption = '%'
  ClientHeight = 285
  ClientWidth = 449
  Color = 16382457
  OnClose = FormClose
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object LogoImage: TUiImage
    Left = 32
    Top = 20
    Width = 113
    Height = 113
    Picture.Data = {TPngImage 57465 bytes}
    Stretch = True
  end
  object ProductNameLbl: TUiLabel
    Left = 149
    Top = 20
    Width = 276
    Height = 25
    Alignment = taCenter
    AutoSize = False
    Caption = '%'
    FontSize = 8
  end
  object EditionLbl: TUiLabel
    Left = 149
    Top = 45
    Width = 276
    Height = 18
    Alignment = taCenter
    AutoSize = False
    Caption = '%'
    FontSize = 3
  end
  object UpdateAvailableLinkLbl: TUiLinkLabel
    Left = 149
    Top = 78
    Width = 276
    Visible = False
    Alignment = taCenter
    AutoSize = False
    Caption = '%'
    FontColor = 12538127
    URL = '%'
    OnClick = UpdateAvailableLinkClick
  end
  object CopyrightLbl: TUiLabel
    Left = 149
    Top = 99
    Width = 276
    Height = 26
    Alignment = taCenter
    AutoSize = False
    Caption = '%'
  end
  object ExpiryLbl: TUiLabel
    Left = 145
    Top = 132
    Width = 284
    Height = 26
    Alignment = taCenter
    AutoSize = False
    Caption = '%'
    Transparent = True
    WordWrap = True
  end
  object NeedRestartLbl: TUiLabel
    Left = 224
    Top = 160
    Width = 218
    Height = 13
    Alignment = taRightJustify
    Caption = '(restart Beyond Compare now to take effect)'
  end
  object VersionEdit: TUiMemo
    Left = 149
    Top = 63
    Width = 276
    Height = 15
    TabStop = False
    Alignment = taCenter
    BorderStyle = bsNone
    Lines.Strings = ('%')
    ParentColor = True
    ReadOnly = True
    TabOrder = 0
    WantReturns = False
  end
  object IsProEdit: TUiCheckBox
    Left = 8
    Top = 158
    Height = 17
    Caption = 'Evaluate &Pro Edition features'
    TabOrder = 1
    OnClick = IsProClick
  end
  object SeparatorPanel: TUiPanel
    Left = 0
    Top = 175
    Width = 449
    Height = 4
    Align = alBottom
    ParentBackground = False
    TabOrder = 2
  end
  object BottomPanel: TUiPanel
    Left = 0
    Top = 179
    Width = 449
    Height = 106
    Align = alBottom
    BevelOuter = bvNone
    Color = 592285
    ParentBackground = False
    TabOrder = 3
    OnPaint = BottomPanelPaint
    object ShowLicenseLinkLbl: TUiLinkLabel
      Left = 350
      Top = 8
      Width = 91
      Visible = False
      Alignment = taRightJustify
      Caption = 'License Agreement'
      FontColor = 12538127
      LinkFontColor = clCream
      URL = '%'
      OnClick = ShowLicenseLinkClick
    end
    object PanelView: TUiActivePanelView
      Left = 8
      Top = 8
      Width = 305
      Height = 90
      ParentColor = True
      TabOrder = 0
      object UnregisteredPanel: TUiActivePanel
        ParentColor = True
        object TrialModeLbl: TUiLabel
          Left = 8
          Top = 8
          Height = 17
          Caption = 'TRIAL MODE'
          StyleElements = [seClient, seBorder]
          FontColor = 11328489
          FontSize = 1
          UseTitleFont = True
        end
        object TrialStatusLbl: TUiLabel
          Left = 8
          Top = 25
          Width = 289
          Height = 52
          AutoSize = False
          Caption = '%'
          WordWrap = True
          StyleElements = [seClient, seBorder]
          FontColor = clCream
        end
      end
      object RegisteredPanel: TUiActivePanel
        ParentColor = True
        object RegisteredToLbl: TUiLabel
          Left = 8
          Top = 8
          Height = 17
          Caption = 'LICENSED TO'
          FocusControl = RegisteredToEdit
          StyleElements = [seClient, seBorder]
          FontColor = 11328489
          FontSize = 1
          UseTitleFont = True
        end
        object RegisteredToEdit: TUiMemo
          Left = 5
          Top = 25
          Width = 295
          Height = 65
          TabStop = False
          BorderStyle = bsNone
          ParentColor = True
          ReadOnly = True
          TabOrder = 0
          WantReturns = False
        end
      end
      object LitePanel: TUiActivePanel
        ParentColor = True
        object LiteDescriptionLbl: TUiLabel
          Left = 8
          Top = 8
          Width = 289
          Height = 65
          AutoSize = False
          Caption = '%'
          WordWrap = True
          StyleElements = [seClient, seBorder]
          FontColor = clCream
        end
      end
    end
    object CloseBtn: TUiCloseBtn
      Left = 368
      Top = 75
      TabOrder = 1
    end
  end
end
