object OpDeleteDialog: TOpDeleteDialog
  HelpType = htKeyword
  HelpKeyword = 'OpDelete'
  Caption = 'Delete'
  ClientHeight = 381
  PixelsPerInch = 96
  TextHeight = 13
  object SelectionPanel: TUiPanel
    object WindowShape: TUiWindowShape
      LeftImageIndex = imgDelete
      RightImageIndex = imgDelete
    end
  end
  object ActionPanel: TUiPanel
    Height = 75
    object ActionDescLbl: TUiLabel
      Left = 8
      Top = 29
      Height = 13
      Caption = 'Delete selected files, folders.'
    end
    object UseRecycleBinEdit: TUiCheckBox
      Left = 8
      Top = 50
      Height = 17
      Caption = '&Use recycle bin if possible'
      TabOrder = 0
      OnClick = UseRecycleBinClick
    end
  end
  object FilteredWarnPanel: TUiPanel
    Top = 222
    Height = 120
    object WarnImage: TUiDlgIcon
      Left = 8
      Top = 80
      IconType = diWarning
    end
    object WarnLbl: TUiLabel
      Left = 48
      Top = 86
      Width = 337
      Height = 13
      Caption = 'Folders with hidden items will not be deleted.'
      WordWrap = True
    end
  end
  object BtnPanel: TUiBtnPanel
    Top = 342
    object OkBtn: TUiOkBtn
      Caption = '&Delete'
    end
  end
end
