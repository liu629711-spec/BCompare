object OpRenameDialog: TOpRenameDialog
  HelpType = htKeyword
  HelpKeyword = 'OpRename'
  Caption = 'Rename'
  ClientHeight = 412
  PixelsPerInch = 96
  TextHeight = 13
  object ActionPanel: TUiPanel
    Height = 146
    object OldMaskLbl: TUiLabel
      Left = 8
      Top = 54
      Height = 13
      Caption = '&Old mask:'
      FocusControl = OldMaskEdit
    end
    object NewMaskLbl: TUiLabel
      Left = 8
      Top = 100
      Height = 13
      Caption = '&New mask:'
      FocusControl = NewMaskEdit
    end
    object IsDOSEdit: TUiRadioButton
      Left = 8
      Top = 29
      Height = 17
      Caption = '&DOS compatible'
      TabOrder = 0
      OnClick = IsRegExpClick
    end
    object IsRegExpEdit: TUiRadioButton
      Left = 200
      Top = 29
      Height = 17
      Caption = 'Regular &expressions'
      TabOrder = 1
      OnClick = IsRegExpClick
    end
    object OldMaskEdit: TUiEdit
      Left = 8
      Top = 71
      Width = 377
      Height = 21
      TabOrder = 2
      OnChange = MaskEditChange
    end
    object NewMaskEdit: TUiEdit
      Left = 8
      Top = 117
      Width = 377
      Height = 21
      TabOrder = 3
      OnChange = MaskEditChange
    end
  end
  object FilteredWarnPanel: TUiPanel
    Top = 293
  end
  object BtnPanel: TUiBtnPanel
    Top = 373
  end
end
