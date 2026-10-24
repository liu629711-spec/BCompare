object OpCopyToDialog: TOpCopyToDialog
  HelpType = htKeyword
  HelpKeyword = 'OpCopyTo'
  Caption = 'Copy to Folder'
  ClientHeight = 425
  PixelsPerInch = 96
  TextHeight = 13
  object SelectionPanel: TUiPanel
    object WindowShape: TUiWindowShape
      LeftImageIndex = imgCopyTo
      RightImageIndex = imgCopyTo
    end
  end
  object ActionPanel: TUiPanel
    Height = 159
    object ActionDescLbl: TUiLabel
      Left = 8
      Top = 29
      Height = 13
      Caption = 'Copy selected files to this &folder:'
      FocusControl = DirEdit
    end
    object DirEdit: TUiSpecComboBar
      Left = 8
      Top = 46
      Width = 377
      AutoCompleteEx = acDirs
      Images = BcImages.MainImages
      SupportsProfile = True
      TabOrder = 0
      OnBrowse = DirEditBrowse
      OnChange = DirEditChange
      OnUpdateTitles = DirEditUpdateTitles
    end
    object DirStructurePanel: TUiPanel
      Left = 0
      Top = 75
      Width = 393
      Height = 84
      Align = alBottom
      BevelOuter = bvNone
      TabOrder = 1
      object DirStructureLbl: TUiLabel
        Left = 8
        Top = 0
        Height = 13
        Caption = 'Folder structure:'
      end
      object DirKeepRelativeEdit: TUiRadioButton
        Left = 8
        Top = 17
        Height = 17
        Caption = 'Keep relati&ve folder structure'
        TabOrder = 0
      end
      object DirKeepBaseEdit: TUiRadioButton
        Left = 8
        Top = 38
        Height = 17
        Caption = 'Keep b&ase folder structure'
        TabOrder = 1
      end
      object DirFlattenEdit: TUiRadioButton
        Left = 8
        Top = 59
        Height = 17
        Caption = '&Don''t keep folder structure'
        TabOrder = 2
      end
    end
  end
  object FilteredWarnPanel: TUiPanel
    Top = 306
  end
  object BtnPanel: TUiBtnPanel
    Top = 386
    object OkBtn: TUiOkBtn
      OnClick = OkClick
    end
  end
end
