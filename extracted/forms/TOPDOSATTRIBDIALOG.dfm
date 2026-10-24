object OpDOSAttribDialog: TOpDOSAttribDialog
  HelpType = htKeyword
  HelpKeyword = 'OpAttrib'
  Caption = 'Attributes'
  ClientHeight = 400
  PixelsPerInch = 96
  TextHeight = 13
  object ActionPanel: TUiPanel
    Height = 134
    object ActionDescLbl: TUiLabel
      Left = 8
      Top = 29
      Width = 377
      Height = 26
      Caption = 'Check a box to set attribute on selected files.  Uncheck a box to clear attribute.'
      WordWrap = True
    end
    object ReadOnlyEdit: TUiCheckBox
      Left = 8
      Top = 63
      Height = 17
      Caption = 'R&ead-only'
      TabOrder = 0
    end
    object HiddenEdit: TUiCheckBox
      Left = 8
      Top = 84
      Height = 17
      Caption = '&Hidden'
      TabOrder = 1
    end
    object ArchiveEdit: TUiCheckBox
      Left = 200
      Top = 63
      Height = 17
      Caption = '&Archive'
      TabOrder = 2
    end
    object SysFileEdit: TUiCheckBox
      Left = 200
      Top = 84
      Height = 17
      Caption = 'S&ystem'
      TabOrder = 3
    end
    object RecursiveEdit: TUiCheckBox
      Left = 8
      Top = 109
      Height = 17
      Caption = 'Including folder &contents'
      TabOrder = 4
      OnClick = RecursiveClick
    end
  end
  object FilteredWarnPanel: TUiPanel
    Top = 281
  end
  object BtnPanel: TUiBtnPanel
    Top = 361
  end
end
