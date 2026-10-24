object TotalCmdrPackerDialog: TTotalCmdrPackerDialog
  Caption = 'Add Total Commander "Packer" Plug-in'
  ClientHeight = 184
  ClientWidth = 363
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object BottomLineBevel: TUiBevel
    Left = 0
    Top = 143
    Width = 363
    Height = 2
    Align = alBottom
    Shape = bsBottomLine
  end
  object PanelView: TUiActivePanelView
    Left = 0
    Top = 0
    Width = 363
    Height = 143
    Align = alClient
    TabOrder = 0
    object FilePanel: TUiActivePanel
      object Lbl: TUiLabel
        Left = 8
        Top = 8
        Width = 340
        Height = 26
        Caption = 'Additional archive types can be supported by adding Total Commander "packer" plug-ins.'
        WordWrap = True
      end
      object FilenameLbl: TUiLabel
        Left = 8
        Top = 42
        Height = 13
        Caption = '&Select "packer" plug-in file:'
        FocusControl = FilenameEdit
      end
      object DownloadLbl: TUiLabel
        Left = 8
        Top = 88
        Height = 13
        Caption = '"Packer" plug-in files are available at:'
      end
      object OfficialLinkLbl: TUiLinkLabel
        Left = 24
        Top = 105
        Height = 13
        Caption = '%'
        URL = '%'
      end
      object UnofficialLinkLbl: TUiLinkLabel
        Left = 24
        Top = 122
        Height = 13
        Caption = '%'
        URL = '%'
      end
      object FilenameEdit: TUiSpecBar
        Left = 8
        Top = 59
        Width = 347
        TabOrder = 0
        OnBrowse = FilenameEditBrowse
        OnChange = SomethingChangedClick
      end
    end
    object ConfirmPanel: TUiActivePanel
      object NameLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'Name:'
      end
      object NameEditLbl: TUiLabel
        Left = 8
        Top = 25
        Height = 13
        Caption = '%'
      end
      object MaskLbl: TUiLabel
        Left = 8
        Top = 46
        Height = 13
        Caption = '&Mask:'
        FocusControl = MaskEdit
      end
      object MaskEdit: TUiEdit
        Left = 8
        Top = 63
        Width = 347
        Height = 21
        TabOrder = 0
      end
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 145
    Width = 363
    TabOrder = 1
    object BackBtn: TUiBackBtn
      OnClick = BackClick
    end
    object NextBtn: TUiNextBtn
      OnClick = NextClick
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
