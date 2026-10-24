object OpBaseDialog: TOpBaseDialog
  BorderIcons = [biSystemMenu, biHelp]
  Caption = '%'
  ClientHeight = 387
  ClientWidth = 393
  OnCloseQuery = FormCloseQuery
  PixelsPerInch = 96
  TextHeight = 13
  object SelectionPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 393
    Height = 147
    BevelOuter = bvNone
    TabOrder = 0
    object SelectionLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'Selection:'
    end
    object LeftFilesLbl: TUiLabel
      Left = 16
      Top = 50
      Height = 13
      Caption = '%'
      ShowAccelChar = False
    end
    object LeftFoldersLbl: TUiLabel
      Left = 16
      Top = 67
      Height = 13
      Caption = '%'
      ShowAccelChar = False
    end
    object LeftTotalBytesLbl: TUiLabel
      Left = 16
      Top = 84
      Height = 13
      Caption = '%'
      ShowAccelChar = False
    end
    object WindowShape: TUiWindowShape
      Left = 147
      Top = 28
      Images = BcImages.MainImages
      LeftImageIndex = imgSelectAll
      RightImageIndex = imgSelectAll
      OnMouseDown = WindowShapeMouseDown
    end
    object RightFilesLbl: TUiLabel
      Left = 261
      Top = 50
      Height = 13
      Caption = '%'
      ShowAccelChar = False
    end
    object RightFoldersLbl: TUiLabel
      Left = 261
      Top = 67
      Height = 13
      Caption = '%'
      ShowAccelChar = False
    end
    object RightTotalBytesLbl: TUiLabel
      Left = 261
      Top = 84
      Height = 13
      Caption = '%'
      ShowAccelChar = False
    end
    object BuildProgressLbl: TUiLabel
      Left = 8
      Top = 126
      Height = 13
      Caption = '%'
    end
    object LeftCheckEdit: TUiCheckBox
      Left = 8
      Top = 29
      Height = 17
      Caption = '&Left side'
      TabOrder = 0
      OnClick = SidesChangedClick
    end
    object LeftRadioEdit: TUiRadioButton
      Left = 8
      Top = 29
      Height = 17
      Caption = '&Left side'
      TabOrder = 1
      OnClick = SidesChangedClick
    end
    object RightCheckEdit: TUiCheckBox
      Left = 253
      Top = 29
      Height = 17
      Caption = '&Right side'
      TabOrder = 2
      OnClick = SidesChangedClick
    end
    object RightRadioEdit: TUiRadioButton
      Left = 253
      Top = 29
      Height = 17
      Caption = '&Right side'
      TabOrder = 3
      OnClick = SidesChangedClick
    end
  end
  object ActionPanel: TUiPanel
    Left = 0
    Top = 147
    Width = 393
    Height = 121
    BevelOuter = bvNone
    TabOrder = 1
    object ActionBevel: TUiBevel
      Left = 8
      Top = 0
      Width = 377
      Height = 1
      Shape = bsTopLine
    end
    object ActionLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'Action:'
    end
  end
  object FilteredWarnPanel: TUiPanel
    Left = 0
    Top = 268
    Width = 393
    Height = 80
    BevelOuter = bvNone
    TabOrder = 2
    object FilteredWarnBevel: TUiBevel
      Left = 8
      Top = 0
      Width = 377
      Height = 1
      Shape = bsTopLine
    end
    object FilteredWarnLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'Filters:'
    end
    object FilteredWarnImage: TUiImage
      Left = 8
      Top = 29
      Width = 16
      Height = 16
      ImageIndex = imgFilters
      Images = BcImages.MainImages
    end
    object FilteredWarnDescLbl: TUiLabel
      Left = 32
      Top = 29
      Width = 353
      Height = 13
      Caption = 'Selected folder(s) contain items hidden by display or file filters.'
      WordWrap = True
    end
    object ShowFilteredBtn: TUiSpeedButton
      Left = 362
      Top = 55
      Hint = 'Show hidden items'
      Flat = False
      ImageIndex = imgPeek
      Images = BcImages.MainImages
      OnClick = ShowFilteredClick
    end
    object IncludeFilteredEdit: TUiCheckBox
      Left = 32
      Top = 55
      Height = 17
      Caption = '&Include hidden items in operation'
      TabOrder = 0
      OnClick = IncludeFilteredClick
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 348
    Width = 393
    TabOrder = 3
    object OkBtn: TUiOkBtn
      Caption = '&Start'
    end
    object CancelBtn: TUiCancelBtn
    end
    object HelpBtn: TUiHelpBtn
    end
  end
end
