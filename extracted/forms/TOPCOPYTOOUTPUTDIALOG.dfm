object OpCopyToOutputDialog: TOpCopyToOutputDialog
  HelpKeyword = 'OpCopyToOutput'
  Caption = 'Copy to Output'
  ClientWidth = 489
  PixelsPerInch = 96
  TextHeight = 13
  object SelectionPanel: TUiPanel
    Width = 489
    object LeftFilesLbl: TUiLabel
      Left = 129
    end
    object LeftFoldersLbl: TUiLabel
      Left = 129
    end
    object LeftTotalBytesLbl: TUiLabel
      Left = 129
    end
    object WindowShape: TUiWindowShape
      Left = 8
      Images = BcImages.ContentImages
      LeftImageIndex = -1
      RightImageIndex = -1
      ShowCenter = True
    end
    object RightFilesLbl: TUiLabel
      Left = 363
    end
    object RightFoldersLbl: TUiLabel
      Left = 363
    end
    object RightTotalBytesLbl: TUiLabel
      Left = 363
    end
    object CenterFilesLbl: TUiLabel
      Left = 246
      Top = 50
      Height = 13
      Caption = '%'
      ShowAccelChar = False
    end
    object CenterFoldersLbl: TUiLabel
      Left = 246
      Top = 67
      Height = 13
      Caption = '%'
      ShowAccelChar = False
    end
    object CenterTotalBytesLbl: TUiLabel
      Left = 246
      Top = 84
      Height = 13
      Caption = '%'
      ShowAccelChar = False
    end
    object LeftCheckEdit: TUiCheckBox
      Left = 121
    end
    object LeftRadioEdit: TUiRadioButton
      Left = 121
    end
    object RightCheckEdit: TUiCheckBox
      Left = 355
      TabOrder = 4
    end
    object RightRadioEdit: TUiRadioButton
      Left = 355
      TabOrder = 5
    end
    object CenterCheckEdit: TUiCheckBox
      Left = 238
      Top = 29
      Height = 17
      Caption = '&Center side'
      TabOrder = 2
      OnClick = SidesChangedClick
    end
    object CenterRadioEdit: TUiRadioButton
      Left = 238
      Top = 29
      Height = 17
      Caption = '&Center side'
      TabOrder = 3
      OnClick = SidesChangedClick
    end
  end
  object ActionPanel: TUiPanel
    Width = 489
    object ActionBevel: TUiBevel
      Width = 473
    end
    object ActionDescLbl: TUiLabel
      Caption = 'Copy selected files and folders to the output folder.'
    end
  end
  object FilteredWarnPanel: TUiPanel
    Width = 489
    object FilteredWarnBevel: TUiBevel
      Width = 473
    end
    object FilteredWarnDescLbl: TUiLabel
      Width = 449
    end
    object ShowFilteredBtn: TUiSpeedButton
      Left = 458
    end
  end
  object BtnPanel: TUiBtnPanel
    Width = 489
    object DontShowAgainBevel: TUiBevel
      Width = 489
    end
  end
end
